import datetime
import logging
import pathlib

from rebel_management_utilities.config.config import get_config
from rebel_management_utilities.utils.mattermost import post_to_channel, LOGGING_CHANNEL_ID, \
    LOCAL_GROUP_INTEGRATORS_CHANNEL_ID
from rebel_management_utilities.utils.members import get_member_stats
from rebel_management_utilities.utils.nextcloud import get_nextcloud_user, BASE_URL, INTEGRATION_DIRECTORY, \
    write_to_spreadsheet, CIRCLE_INTEGRATION_DIRECTORY

logging.getLogger().setLevel(logging.INFO)


def get_spreadsheet_url(base_directory, group):
    username = get_nextcloud_user()
    group_safe = ''.join(e for e in group if e.isalnum()).replace('â', 'a')
    filename = f'New rebels {group_safe}.xlsx'
    return BASE_URL + username + base_directory + group_safe + '/' + filename


def push_spreadsheet(df, group, base_directory):
    try:
        url = get_spreadsheet_url(base_directory, group)
        df_formatted = df[['submission_date', 'name', 'email_address', 'phone_number', 'municipality',
                           'form_name', 'taggings', 'comments']].sort_values('submission_date')

        df_formatted = df_formatted.rename(columns={'name': 'Naam', 'email_address': 'E-mail',
                                                    'phone_number': 'Telefoon', 'municipality': 'Gemeente',
                                                    'form_name': 'Aangemeld via', 'taggings': 'Interesses',
                                                    'submission_date': 'Aangemeld op', 'comments': 'Commentaar'})

        write_to_spreadsheet(url, df_formatted, deduplicate_column='E-mail')
        post_to_channel(LOGGING_CHANNEL_ID,
                        f'Successfully updated integrator spreadsheet for {group} - {len(df_formatted)} new rebels')
    except Exception as e:
        logging.warning(f'Failed to update integrator spreadsheet for {group} - {e}')
        post_to_channel(LOGGING_CHANNEL_ID, f'@all Failed to update integrator spreadsheet for {group} - {e}')


def post_signups_to_mattermost(df, lookback_days):
    df_grouped = df.groupby('local_group').size()
    total_signups = df_grouped.sum()
    df_grouped = df_grouped.reset_index().rename(columns={'local_group': 'Local group', 0: '#'})

    with open(pathlib.Path(__file__).parent / 'resources/signups_message.md', 'r') as f:
        message = f.read()

    message = message.format(total_signups=total_signups, signup_table=df_grouped.to_markdown(index=False),
                             lookback_days=lookback_days)

    post_to_channel(LOCAL_GROUP_INTEGRATORS_CHANNEL_ID, message)


if __name__ == "__main__":
    lookback_days = get_config()['lookback_days']

    start_date = datetime.date.today() - datetime.timedelta(days=lookback_days)
    df = get_member_stats(start_date)

    for local_group, df_grouped in df.groupby('local_group'):
        push_spreadsheet(df_grouped, local_group, INTEGRATION_DIRECTORY)

    for circle, circle_config in get_config()['circles'].items():
        df_grouped = df[df['taggings'].apply(lambda x: circle_config["tagging"] in x)]
        push_spreadsheet(df_grouped, circle, CIRCLE_INTEGRATION_DIRECTORY)

    push_spreadsheet(df[df['local_group'].isnull()], 'Other', INTEGRATION_DIRECTORY)

    post_signups_to_mattermost(df, lookback_days)
