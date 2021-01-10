import os

import pandas as pd
import requests
from dotenv import load_dotenv
from filecache import filecache

from local_group_support.config.config import get_config

API_URL = 'https://actionnetwork.org/api/v2/'


def load_api_key():
    load_dotenv()
    key = os.getenv("ACTION_NETWORK_API_KEY")

    if not key:
        raise OSError('ACTION_NETWORK_API_KEY not found in .env')

    return key


@filecache(24 * 60 * 60)
def query(endpoint=None, url=None):
    if url is None:
        url = API_URL + endpoint
    headers = {'OSDI-API-Token': load_api_key()}

    print(f'Querying {url}')
    response = requests.get(url, headers=headers)
    status_code = response.status_code
    if status_code != 200:
        raise requests.HTTPError(response=response)
    return response.json()


@filecache(24 * 60 * 60)
def query_all(endpoint):
    responses = []
    url = API_URL + endpoint
    headers = {'OSDI-API-Token': load_api_key()}
    print(url)

    while True:
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        print(response)
        if status_code != 200:
            raise requests.HTTPError(response=response)
        res = response.json()
        content = next(iter(res['_embedded'].values()))
        responses.extend(content)
        try:
            url = res['_links']['next']['href']
        except KeyError:  # end querying when there is no more data left
            break

    return responses


def get_forms():
    forms = query_all(endpoint='forms')

    form_df = []

    for form in forms:
        for identifier in form['identifiers']:
            form_df.append({'name': form['name'],
                            'title': form['title'],
                            'identifier': identifier.split(':')[1],
                            'total_submissions': form['total_submissions'],
                            'browser_url': form['browser_url'],
                            'created_date': form['created_date'],
                            'modified_date': form['modified_date'],
                            'creator': form['_embedded']['osdi:creator']
                            })

    return pd.DataFrame(form_df)


def get_messages():
    messages = query_all(endpoint='messages')
    df = pd.DataFrame(messages)

    def get_stats(row):
        stats = row['statistics']
        if type(stats) is dict:
            return stats
        return {}

    df = pd.concat([df, df.apply(get_stats, axis=1, result_type='expand')], axis=1)

    df['clicked_ratio'] = df['clicked'] / df['opened']
    df['opened_ratio'] = df['opened'] / df['sent']
    df['local_group'] = df.apply(get_local_group, axis=1)
    df['date'] = pd.to_datetime(df['created_date']).dt.date
    return df
