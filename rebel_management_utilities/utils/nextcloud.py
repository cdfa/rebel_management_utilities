import os

import requests
from appdirs import user_cache_dir
from dotenv import load_dotenv

from rebel_management_utilities.utils.excel import append_df_to_excel

BASE_URL = 'https://cloud.extinctionrebellion.nl/remote.php/dav/files/'
INTEGRATION_DIRECTORY = '/CloudXRNL/AppSpecific/Integrators_AN_Home/Integrators_FromLGs/'
CIRCLE_INTEGRATION_DIRECTORY = '/CloudXRNL/AppSpecific/Integrators_AN_Home/Integrators_FromCircles/'


def get_nextcloud_user():
    load_dotenv()
    key = os.getenv("NEXTCLOUD_USER")

    if not key:
        raise OSError('NEXTCLOUD_USER not found in .env')

    return key


def get_nextcloud_password():
    load_dotenv()
    key = os.getenv("NEXTCLOUD_PASSWORD")

    if not key:
        raise OSError('NEXTCLOUD_PASSWORD not found in .env')

    return key


def write_to_spreadsheet(url, data, deduplicate_column=None):
    if deduplicate_column:
        data = data.drop_duplicates(subset=deduplicate_column)

    auth = (get_nextcloud_user(), get_nextcloud_password())
    response = requests.get(url, auth=auth)
    file_name = user_cache_dir('rebel_management_utilities', 'XR NL') + '/' + 'tmp.xlsx'

    with open(file_name, 'wb') as f:
        f.write(response.content)

    append_df_to_excel(file_name, data, deduplicate_column=deduplicate_column, skiprows=1, header=False, index=False)

    with open(file_name, 'rb') as f:
        data = f.read()
        requests.put(url, data=data, auth=auth)
