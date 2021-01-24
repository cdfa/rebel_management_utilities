import pandas as pd

from rebel_management_utilities.utils.mattermost import post_to_channel, LOGGING_CHANNEL_ID
from rebel_management_utilities.utils.members import get_ags
from rebel_management_utilities.utils.nextcloud import AFFINITY_GROUPS_DIRECTORY, get_nextcloud_user, BASE_URL, \
    write_to_spreadsheet


def get_spreadsheet_url(base_directory, group):
    username = get_nextcloud_user()
    group_safe = ''.join(e for e in group if e.isalnum()).replace('â', 'a')
    filename = f'Affinity groups {group_safe}.xlsx'
    return BASE_URL + username + base_directory + group_safe + '/' + filename


def push_spreadsheet(df, group, base_directory):
    try:
        url = get_spreadsheet_url(base_directory, group)
        df_formatted = df[
            ['AG_name', 'AG_size', 'AG_n_arrestables', 'AG_regen_phone', 'Municipality', 'AG_comment']].sort_values(
            'submission_date')

        df_formatted = df_formatted.rename(columns={'AG_name': 'Naam', 'AG_size': '# rebels',
                                                    'AG_n_arrestables': '# arrestables',
                                                    'AG_regen_phone': 'Telefoon', 'Municipality': 'Gemeente',
                                                    'AG_comment': 'Commentaar'})

        write_to_spreadsheet(url, df_formatted, deduplicate_column='E-mail')
        post_to_channel(LOGGING_CHANNEL_ID,
                        f'Successfully updated affinity groups for {group}')
    except Exception as e:
        post_to_channel(LOGGING_CHANNEL_ID, f'@all Failed to update affinity groups for {group} - {e}')


if __name__ == "__main__":
    ags = pd.DataFrame(get_ags())

    for local_group, ags_grouped in ags.groupby('local_group'):
        push_spreadsheet(ags_grouped, local_group, AFFINITY_GROUPS_DIRECTORY)
