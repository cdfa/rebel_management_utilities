import datetime

import pandas as pd

from rebel_management_utilities.config.config import get_config
from rebel_management_utilities.utils.action_network import get_forms, query, query_all

FORMATION_DATE = datetime.date(2018, 4, 1)


def get_form(submission):
    form_id = submission['action_network:form_id']
    has_website = 'action_network:referrer_data' in submission.keys() and \
                  submission['action_network:referrer_data']['source'] != 'none'
    form_mapping = get_forms().set_index('identifier')['name']
    submission_date = pd.to_datetime(submission['created_date']).date()

    form_name = 'Other'
    sign_up_channel = 'Other'

    if form_id in form_mapping.keys():
        form_name = form_mapping[form_id]

    if 'NVDA' in form_name:
        sign_up_channel = 'NVDA'

    if 'Volunteer' in form_name:
        sign_up_channel = 'Attended introduction meeting'

    if 'Join' in form_name:
        if has_website and submission_date < datetime.date(2020, 2, 20):
            sign_up_channel = 'Website'
        else:
            sign_up_channel = 'Attended Talk'

    if 'Website' in form_name:
        sign_up_channel = 'Website'

    if 'Join Affinity Group' in form_name:
        sign_up_channel = 'Looking for Affinity group'

    return {'form_name': form_name, 'sign_up_channel': sign_up_channel, 'form_id': form_id,
            'submission_date': submission_date}


def get_member_forms(member):
    submissions = query(url=member['_links']['osdi:submissions']['href'])

    forms = []
    for submission in submissions['_embedded']['osdi:submissions']:
        forms.append(get_form(submission))

    return forms


def get_custom_field(member, field):
    return member['custom_fields'].get(field)


def get_local_group(member):
    municipality = get_custom_field(member, 'Municipality')
    config = get_config()
    for local_group, local_group_config in config['local_groups'].items():
        if municipality in local_group_config['municipalities']:
            return local_group


def get_email_address(member):
    for email in member['email_addresses']:
        if email['primary']:
            return email['address']


def get_member_taggings(member):
    taggings = query(url=member['_links']['osdi:taggings']['href'])
    tag_names = []

    for tagging in taggings['_embedded']['osdi:taggings']:
        tag = query(url=tagging['_links']['osdi:tag']['href'])
        tag_names.append(tag['name'])

    return tag_names


def get_ags():
    """
        Returns a list of all AG's. Format of an AG:
            {'AG_name': '',
            'AG_size': '',
            'AG_n_non_arrestables': '',
            'AG_n_arrestables': ''',
            'Municipality': '',
            'phone_number': '',         # rep phone number.
            'AG_regen_phone': '',
            'AG_comments': '',
            'given_name': ''}           # rep name.
    """
    # Hardcoded AN endpoints for AG forms creation/update forms.
    an_ag_endpoints = [
        "forms/e8ac2f14-ba65-47fc-9560-90bd17f105fc/submissions",
        "forms/d38377d0-be06-4853-ae82-06d0425e4918/submissions",
        "forms/dac52069-261e-4485-8124-8e075dc84890/submissions",
        "forms/8db3db83-38b1-4b9b-8251-6ef672f5cfaa/submissions"
    ]

    # Get the endpoints to the people who signed the form - they hold the AG info.
    people_endpoints = []
    for endpoint in an_ag_endpoints:
        people_endpoints += [p["_links"]["osdi:person"]["href"] for p in query_all(endpoint)]

    # Request the AG data through these endpoints.
    ags = []
    for url in list(set(people_endpoints)): # Remove duplicates (because of update form.)
        response = query(url=url)
        ag = {}

        # Format the AG data.
        for field in ["AG_name", "AG_size", "AG_n_non_arrestables", "AG_n_arrestables", "Municipality", "phone_number", "AG_regen_phone", "AG_comments"]:
            if field not in response["custom_fields"]:
                response["custom_fields"][field] = ""
            ag[field] = response["custom_fields"][field]
        if "given_name" not in response:
            response["given_name"] = ""
        ag["given_name"] = response["given_name"]
        ag["created_date"] = pd.to_datetime(response["created_date"]).date()
        ag["local_group"] = get_local_group(response)
        ag["email_address"] = get_email_address(response)
        ags.append(ag)
    return ags


def extract_data(member):
    name = member.get('given_name')
    email_address = get_email_address(member)
    phone_number = get_custom_field(member, 'Phone number')
    languages_spoken = member.get('languages_spoken')
    sign_up_date = pd.to_datetime(member['created_date']).date()
    modified_date = pd.to_datetime(member['modified_date']).date()

    if sign_up_date < FORMATION_DATE:
        sign_up_date = pd.NaT
    forms = get_member_forms(member)
    local_group = get_local_group(member)
    municipality = get_custom_field(member, 'Municipality')
    taggings = get_member_taggings(member)
    comments = get_custom_field(member, 'comments')
    return [{'name': name, 'local_group': local_group, 'municipality': municipality, 'sign_up_date': sign_up_date,
             'modified_date': modified_date,
             'languages_spoken': languages_spoken, 'email_address': email_address,
             'taggings': taggings, 'comments': comments,
             'phone_number': phone_number, **form} for form in forms]


def get_member_stats(start_date):
    members = query_all(endpoint='people')

    members_processed = []

    for index, m in enumerate(members):
        print(f'Processing {index} of {len(members)}')
        if pd.to_datetime(m['modified_date']).date() <= start_date:
            continue
        members_processed.extend(extract_data(m))

    df = pd.DataFrame(members_processed)
    return df


def get_local_group_overview(to_file=False):
    """
        Returns two dicts: one mapping local groups to the number of people in them
        and one mapping municipalities to the number of people in them.

        Only includes municipalities and local groups with at least one sign-up.

        Also saves this data to the 'local_group_sizes.csv' and 'municipality_sizes.csv'
        files if 'to_file' is set.
    """
    municipalities = {}
    local_groups = {}

    for p in query_all(endpoint='people'):

        local_group = get_local_group(p)
        try:
            municipality = p["custom_fields"]["Municipality"]
        except Exception as e:
            continue
        if municipality not in municipalities:
            municipalities[municipality] = 0
        if local_group not in local_groups:
            local_groups[local_group] = 0
        municipalities[municipality] += 1
        local_groups[local_group] += 1

    if to_file:
        with open('local_group_sizes.csv', 'w') as f:
            for k in local_groups.keys():
                f.write("%s, %s\n" % (k, local_groups[k]))
        with open('municipality_sizes.csv', 'w') as f:
            for k in municipalities.keys():
                f.write("%s, %s\n" % (k, municipalities[k]))

    return local_groups, municipalities