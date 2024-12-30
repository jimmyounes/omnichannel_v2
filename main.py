from src.google_analytics.data_extract import  *
from src.analyse.data_process import * 
from src.models.lstm_model import * 
from src.models.new_markov_model import * 
from src.models.old_markov_model import *
from src.insights.define_functions import * 
import asyncio
from dotenv import load_dotenv
import os
import json
import time

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
    """
    Extract data
    """
    start_time_process = time.time()
    start_time = time.time()
    data=await fetching_main_process(dimensions,metriques,start_date,end_date,filter,
                          access_token,refresh_token,client_id,
                          client_secret,DISCOVERY_URL,property_id)
    #with open("data_property10.json","r") as file :
    #    data=json.load(file)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Extraction data  took {elapsed_time:.2f} seconds to execute.")

    """
    Cleaning data extracted 
    """
    start_time = time.time()

    date_list=generate_range_dates(start_date,end_date)
    users_journey=get_users_path(data) 
    users_journey=deleting_first_week(users_journey,date_list)  
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"data cleaning  took {elapsed_time:.2f} seconds to execute.")
 
    """
    Building paths  
    """
    start_time = time.time()

    purchase_by_date,date_autonomous_results=assembly_purchases_by_date(users_journey)
    purchase_by_date,date_autonomous_results=paths_cleaning_by_date(purchase_by_date,date_autonomous_results) 

    data = []
    for date, transitions in purchase_by_date.items():
        for transition, metrics in transitions.items():
            row = {"date": date, "path": transition,"multipath":True, **metrics}
            data.append(row)
    for date, transitions in date_autonomous_results.items():
        for transition, metrics in transitions.items():
            row = {"date": date, "path": transition,"multipath":False, **metrics}
            data.append(row)

    df = pd.DataFrame(data)
    df.to_excel("purchased_by_date.xlsx")

    paths=build_journey_paths(users_journey)
    paths,autonomous_paths=paths_cleaning(paths)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Building paths  took {elapsed_time:.2f} seconds to execute.")

    """
    extract analyse summary 
    """
    start_time = time.time()
    list_sommet,noeuds=channels_roles(paths)
    """
    lstm training
    """
    start_time = time.time()
    lstm_attribution,representation_binaire=lstm_model(paths,noeuds)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"lstm training  took {elapsed_time:.2f} seconds to execute.")
    
    results=analyse_summary(paths,autonomous_paths,noeuds)
    matrice=synergy_between_channels(paths,noeuds)
    dimension_path_by_channel=dimensions_path_by_channels(noeuds,paths)
    results_autonomous=get_dimensions_autonomous(autonomous_paths)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Extract summary analyse  took {elapsed_time:.2f} seconds to execute.")
    df = pd.DataFrame([matrice])
    df.to_excel("synergy_channels.xlsx")
    df = pd.DataFrame([results])
    df.to_excel("analyseSummary.xlsx")
    df_analyse = pd.DataFrame.from_dict(list_sommet, orient="index").reset_index()
    df_analyse = df_analyse.rename(columns={"index": "channel"})
    df_analyse.to_excel("channels_overview.xlsx")
    df_analyse = pd.DataFrame.from_dict(dimension_path_by_channel, orient="index").reset_index()
    df_analyse = df_analyse.rename(columns={"index": "channel"})
    df_analyse.to_excel("dimension_path_by_channel.xlsx")
    df_analyse = pd.DataFrame.from_dict(results_autonomous, orient="index").reset_index()
    df_analyse = df_analyse.rename(columns={"index": "channel"})
    df_analyse.to_excel("channel_autonomous.xlsx")
    df_analyse = pd.DataFrame.from_dict(paths, orient="index").reset_index()
    df_analyse = df_analyse.rename(columns={"index": "path"})
    df_analyse.to_excel("paths_overview.xlsx")
    

    """
    New and old markov chain process 
    """

    new_omnichannel=new_process_omnichannel(paths,noeuds)
    old_attribution=old_process_omnichannel(paths,noeuds)

    """
    LSTM model overview 
    """
    start_time = time.time()

    #lstm_attribution,representation_binaire=lstm_model(paths,noeuds)
    paths_lstm=optimize_paths(paths, lstm_attribution, representation_binaire)
    lstm_attribution=attribuate_conv_to_channels(paths_lstm)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"lstm process   took {elapsed_time:.2f} seconds to execute.")
    
    attribuate_models=attribuate_conv_turnover_to_channels(noeuds,old_attribution,new_omnichannel,lstm_attribution,results["multichannels_conversions"],results["multichannels_purchase_value"])
    df_analyse = pd.DataFrame.from_dict(attribuate_models, orient="index").reset_index()
    df_analyse = df_analyse.rename(columns={"index": "channel"})
    df_analyse.to_excel("channels_model_attribution.xlsx")
    end_time = time.time()
    elapsed_time = end_time - start_time_process

    print(f"All the process   took {elapsed_time:.2f} seconds to execute.")
import asyncio
asyncio.run(main())
