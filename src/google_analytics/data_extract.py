"""
This module handles data extraction for Google Analytics.

It includes functions for authenticating with the Google Analytics API,
retrieving data, and processing it for further analysis.
"""
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build_from_document
import math
import asyncio
import pandas as pd

def generate_range_dates(start_date,end_date):
    """""
    Generate a list of all dates between two dates 
    """
    date_range = pd.date_range(start=start_date, end=end_date)
    date_list = date_range.strftime('%Y-%m-%d').tolist()
    return date_list

def sync_run_report(service, property_id, request):
    """""
    Define google analytics service . 
    """
    return service.properties().runReport(
        property=f'properties/{property_id}', body=request).execute()

def chunk_data_list(data_list, chunk_size):
    """
    Divide data_list into chunks of size chunk_size.
    """
    for i in range(0, len(data_list), chunk_size):
        yield data_list[i:i + chunk_size]

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

async def fetch_analytics_data(dimensions,metriques,start_date,
                               end_date,filter,credentials,
                               property_id,discovery_document):
    """
    Define google analytics service .
    """
    limit = 25000
    try:
        service = build_from_document(discovery_document, credentials=credentials)
        request = {
            'dateRanges': [{"startDate": start_date, "endDate": end_date}],
            'metrics': [metriques],
            'dimensions': dimensions,
            'dimension_filter': {"filter": filter},
            'limit': limit,
            'offset': 0
        }
        response = await asyncio.to_thread(sync_run_report, service, property_id, request)
        nb_run = math.ceil(int(response['rowCount']) / limit)
        while nb_run > 1:
            request["offset"] = limit * (nb_run - 1)
            resp_offset = await asyncio.to_thread(sync_run_report, service, property_id, request)
            response["rows"].extend(resp_offset["rows"])
            nb_run -= 1
            print(f"Remaining pages: {nb_run}")
        return response

    except Exception as er:
        print("ERROR:", er)
        return None


async def fetching_data_process_day_by_day(date_list,dimensions,metriques,filter,
                          discovery_document,credentials,property_id):
    """
    Ruequesting google analytics data day by day .
    """
    data={}
    for date in date_list:
        if  not  data :
            data = await  fetch_analytics_data(dimensions,metriques,date,date,
                                            filter,credentials,property_id,
                                              discovery_document)
        else:
            result=await fetch_analytics_data(dimensions,metriques,date,date,
                                            filter,credentials,property_id,
                                              discovery_document)
            data['rows'].extend(result['rows'])

    return data

async def fetching_main_process(dimensions,metriques,start_date,end_date,filter,
                          access_token,refresh_token,client_id,
                          client_secret,DISCOVERY_URL,property_id):
    """
    Asynchronous function to retreive data from google analytics between two dates for defined dimension and metrics .
    """

    discovery_document = fetch_discovery_document(DISCOVERY_URL)
    credentials=get_credentials(access_token,refresh_token,client_id,client_secret)
    data_list=generate_range_dates(start_date,end_date)
    data_chunks = list(chunk_data_list(data_list, chunk_size=10))
    tasks = [
        fetching_data_process_day_by_day(
            date_chunk, dimensions, metriques, filter,
            discovery_document, credentials, property_id
        )
        for date_chunk in data_chunks
    ]
    results = await asyncio.gather(*tasks)
    combined_data = {"rows": []}
    for result in results:
        if "rows" in result:
            combined_data["rows"].extend(result["rows"])
    return combined_data
