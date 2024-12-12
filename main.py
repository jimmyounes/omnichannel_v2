from src.google_analytics.data_extract import  *

from dotenv import load_dotenv
import os

load_dotenv()
DISCOVERY_URL = 'https://analyticsdata.googleapis.com/$discovery/rest?version=v1beta'
property_id = "310657915"
access_token = os.getenv('ACCESS_TOKEN')
refresh_token = os.getenv("REFRESH_TOKEN")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
dimensions=[{'name':'dateHourMinute'}, {'name': 'eventName'},{'name': 'sessionSourceMedium'},{'name': 'customUser:clientid'} ]
filter= {"fieldName": 'eventName',"inListFilter":{"values": ["purchase","session_start"]}}
start_date="14daysAgo"
end_date="yesterday"

fetching_data_process(dimensions,start_date,end_date,filter,
                          access_token,refresh_token,client_id,
                          client_secret,DISCOVERY_URL,property_id)

