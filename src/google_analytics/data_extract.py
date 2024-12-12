"""
This module handles data extraction for Google Analytics.

It includes functions for authenticating with the Google Analytics API,
retrieving data, and processing it for further analysis.
"""

import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build_from_document
import math
import asyncio

def get_credentials(access_token,refresh_token,client_id,client_secret):  
    credentials = Credentials.from_authorized_user_info({
        'token': access_token,
        'refresh_token': refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': ['https://www.googleapis.com/auth/analytics.readonly']
    })
    return credentials

def fetch_discovery_document(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

async def fetch_analytics_data(dimensions,start_date,
                               end_date,filter,credentials,
                               property_id,discovery_document):
    limit = 25000
    try:
        service = build_from_document(discovery_document, credentials=credentials)
        request = {
        'dateRanges': [{"startDate":start_date, "endDate":end_date}],
        'metrics': [],
        'dimensions': dimensions,
        'dimension_filter' :{"filter" :filter},
        'limit': limit,
        'offset': 0
        }
        response = service.properties().runReport(
            property=f'properties/{property_id}', body=request).execute()
        nb_run = math.ceil(int(response['rowCount'])/limit)
        while nb_run != 1:
            request["offset"] = limit*(nb_run-1)
            resp_offset = service.properties().runReport(
            property=f'properties/{property_id}', body=request).execute()
            response["rows"].extend(resp_offset["rows"])
            nb_run = nb_run-1
            print(nb_run)
        return response
    except Exception as er:
        print("ERROR", er)

def fetching_data_process(dimensions,start_date,end_date,filter,
                          access_token,refresh_token,client_id,
                          client_secret,DISCOVERY_URL,property_id):
    
    discovery_document = fetch_discovery_document(DISCOVERY_URL)
    credentials=get_credentials(access_token,refresh_token,client_id,client_secret)
    data = asyncio.run(fetch_analytics_data(dimensions,start_date,end_date,
                                            filter,credentials,property_id,
                                              discovery_document))
    with open('data_property.json', 'w') as file:
        json.dump(data, file)  
    return data    
