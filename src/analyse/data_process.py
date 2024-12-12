"""""
File that processes retrieved Google Analytics data to construct conversion paths 

"""
import itertools
from utils.script import *


def get_users_path(data):
    """"
    This function enables mapping out the user's journey path. 
    """
    users_dict={}
    for result in data["rows"]:
        item=result['dimensionValues']
        if item[3]["value"] not in users_dict:
            users_dict[item[3]["value"]]=[]
        users_dict[item[3]["value"]].append(
            {
            "date" : item[0]["value"],
            "event" : item[1]["value"],
            "source" : item[2]["value"]})   
    return users_dict

def build_journey_paths(users_journey):
    """""
    Builds journey path with dimensions viewed and purchased and average time to convert 
    """
    for user in users_journey:
        users_journey[user]=sorted(users_journey[user], key=lambda x: x['date'])
    paths={}
    for user in users_journey:
        path=""
        for touchpoint in users_journey[user]:
            touchpoint["source"]=touchpoint["source"].strip()
            if path == "":
                path=touchpoint["source"]
                date1=touchpoint["date"]
            else:
                path=path +"=>"+ touchpoint["source"]
            if touchpoint["event"]=="purchase":
                date2=touchpoint["date"]
                difference=difference_date(date1,date2)
                if path not in paths:
                    paths[path]={}
                    paths[path]["purchased"]=0
                    paths[path]["viewed"]=0
                    paths[path]["time_to_purchase"]=[]
                paths[path]["purchased"]+=1
                paths[path]["time_to_purchase"].append(difference)
                path=""
        if path!="":
            if path not in paths:
                paths[path]={}
                paths[path]["purchased"]=0
                paths[path]["viewed"]=0
                paths[path]["time_to_purchase"]=[]
            paths[path]["viewed"]+=1
    return paths

def paths_cleaning(paths):
    """""
    Remove  (direct/(None) effect from  paths and defines autonomous paths, 
    and calculate average time to purchase
    """
    autonomous_paths={}
    for path in paths:
        nodes = path.split("=>")
        if len(nodes)==1:
            autonomous_paths[path]=paths[path]
        else:
            key = nodes[0].strip()
            autonomous = True
            for i in range(1,len(nodes)):
                if key!=nodes[i].strip():
                    autonomous = False
                    break
            if autonomous is True:
                autonomous_paths[path]=paths[path]
    for path in autonomous_paths:
        del paths[path]
    path_without_direct={}
    for path in paths :
        original_path=path
        path=path.replace("=>(direct) / (none)=>","=>")
        path=path.replace("(direct) / (none)=>","")
        path=path.replace("=>(direct) / (none)","")
        if path!="":
            if path not in path_without_direct:
                path_without_direct[path]=paths[original_path]
            else:
                path_without_direct[path]["purchased"]+=paths[original_path]["purchased"]
                path_without_direct[path]["viewed"]+=paths[original_path]["viewed"]
                path_without_direct[path]["time_to_purchase"] = list(itertools.chain(
                    paths[original_path]["time_to_purchase"],
                    path_without_direct[path]["time_to_purchase"]))
    for path in path_without_direct:
        if path_without_direct[path]["time_to_purchase"]:
            avg_time_to_purchase = sum(path_without_direct[path]["time_to_purchase"]) /len(path_without_direct[path]["time_to_purchase"])
        else:
            avg_time_to_purchase = None
        path_without_direct[path]["avg_time_to_purchase"]=avg_time_to_purchase
    return path_without_direct,autonomous_paths

"""""
import json
with open("data_property.json","r")as file:
    data=json.load(file)
users_journey=get_users_path(data)
paths=build_journey_paths(users_journey)
paths,autonomous_paths=paths_cleaning(paths)
for path in paths:
    print(path)
"""    