from src.google_analytics.data_extract import  *
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
DISCOVERY_URL = 'https://analyticsdata.googleapis.com/$discovery/rest?version=v1beta'
property_id = "310657915"
access_token = os.getenv('ACCESS_TOKEN')
refresh_token = os.getenv("REFRESH_TOKEN")
client_id = os.getenv("CLIENT_ID")
metriques=[{'name': 'eventValue'},{'name': 'eventCount'}]
client_secret = os.getenv("CLIENT_SECRET")
dimensions=[{'name':'dateHourMinute'}, {'name': 'eventName'},{'name': 'sessionSourceMedium'},{'name': 'customUser:clientid'} ]
filter= {"fieldName": 'eventName',"inListFilter":{"values": ["purchase","session_start"]}}
start_date="2024-10-10"
end_date="2024-12-17"
async def main():
    data=await fetching_main_process(dimensions,metriques,start_date,end_date,filter,
                          access_token,refresh_token,client_id,
                          client_secret,DISCOVERY_URL,property_id)
    with open('data_property9.json', 'w') as file:
        json.dump(data, file) 
import asyncio
asyncio.run(main())
