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
            "source" : item[2]["value"],
            "purchase_value": result["metricValues"][0]["value"] 
            })
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
                    paths[path]["purchase_value"]=0
                paths[path]["purchased"]+=1
                paths[path]["purchase_value"]+=float(touchpoint["purchase_value"])
                paths[path]["time_to_purchase"].append(difference)
                path=""
        if path!="":
            if path not in paths:
                paths[path]={}
                paths[path]["purchased"]=0
                paths[path]["viewed"]=0
                paths[path]["time_to_purchase"]=[]
                paths[path]["purchase_value"]=0
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
        if path!="" and  path_is_autonomous(path)==False:
            if path not in path_without_direct:
                path_without_direct[path]=paths[original_path]
            else:
                path_without_direct[path]["purchased"]+=paths[original_path]["purchased"]
                path_without_direct[path]["purchase_value"]+=paths[original_path]["purchase_value"]
                path_without_direct[path]["viewed"]+=paths[original_path]["viewed"]
                path_without_direct[path]["time_to_purchase"] = list(itertools.chain(
                    paths[original_path]["time_to_purchase"],
                    path_without_direct[path]["time_to_purchase"]))
        else :
            if(path_is_autonomous(path)):
                if path not in autonomous_paths:
                    autonomous_paths[path]=paths[original_path]
                else:
                    autonomous_paths[path]["purchased"]+=paths[original_path]["purchased"]
                    autonomous_paths[path]["purchase_value"]+=paths[original_path]["purchase_value"]
                    autonomous_paths[path]["viewed"]+=paths[original_path]["viewed"]
                    autonomous_paths[path]["time_to_purchase"] = list(itertools.chain(
                        paths[original_path]["time_to_purchase"],
                        autonomous_paths[path]["time_to_purchase"]))

    for path in path_without_direct:
        if path_without_direct[path]["time_to_purchase"]:
            avg_time_to_purchase = sum(path_without_direct[path]["time_to_purchase"]) /len(path_without_direct[path]["time_to_purchase"])
        else:
            avg_time_to_purchase = None
        path_without_direct[path]["avg_time_to_purchase"]=avg_time_to_purchase
    for path in autonomous_paths:
        if autonomous_paths[path]["time_to_purchase"]:
            avg_time_to_purchase = sum(autonomous_paths[path]["time_to_purchase"]) /len(autonomous_paths[path]["time_to_purchase"])
        else:
            avg_time_to_purchase = None
        autonomous_paths[path]["avg_time_to_purchase"]=avg_time_to_purchase    
    return path_without_direct,autonomous_paths

def assembly_purchases_by_date(users_dict):
    """""
    Assembly purchases by date
    """
    date_autonomous_results={}
    date_results={}
    for user in users_dict:
        path=""
        for touchpoint in users_dict[user]:
            touchpoint["source"]=touchpoint["source"].strip()
            if path=="":
                path=touchpoint["source"]
            else :
                path=path +"=>"+ touchpoint["source"]
            if touchpoint["event"]=="purchase":
                date2=touchpoint["date"]
                date2=transform_date(date2)
                nodes = path.split("=>")
                key = nodes[0].strip()
                autonomous = True
                for i in range(1,len(nodes)):
                    if key!=nodes[i].strip():
                        autonomous = False
                        break
                if autonomous is False:
                    if date2 not in date_results:
                        date_results[date2]={}
                    if path not in date_results[date2]:
                        date_results[date2][path]={}
                        date_results[date2][path]["purchased"]=1
                        date_results[date2][path]["purchase_value"]=touchpoint["purchase_value"]
                    else:
                        date_results[date2][path]["purchased"]+=1
                        date_results[date2][path]["purchase_value"]+=touchpoint["purchase_value"]
                    path=""
                else:
                    if date2 not in date_autonomous_results:
                        date_autonomous_results[date2]={}
                    if path not in date_autonomous_results[date2]:
                        date_autonomous_results[date2][path]={}
                        date_autonomous_results[date2][path]["purchased"]=1
                    else:
                        date_autonomous_results[date2][path]["purchased"]+=1
                    path=""
    return date_results,date_autonomous_results

def compute_conv_for_channel_in_autonomous_paths(autonomous_path):
    """
    Calculate number of conversions and purchase value  for channel in autonomous path 
    """
    channels_autonomous={}
    for path in autonomous_path :
        key = path.split("=>")
        channel = key[0].strip()
        if channel in channels_autonomous:
            channels_autonomous[channel]["purchased"] += autonomous_path[path]["purchased"] + channels_autonomous[channel]["purchased"]
            channels_autonomous[channel]["purchase_value"] += autonomous_path[path]["purchase_value"] + channels_autonomous[channel]["purchase_value"]
        else :
            channels_autonomous[channel] ={}
            channels_autonomous[channel]["purchased"] =  autonomous_path[path]["purchased"]
            channels_autonomous[channel]["purchase_value"] = autonomous_path[path]["purchase_value"]
    return channels_autonomous

def channels_roles(multichannel_paths):
    """
    Define number of conversions and purchase value for channels in each roles 
    """
    noeuds=[]
    for path in multichannel_paths:
        path=path.split("=>")
        for noeud in path:
            noeud=noeud.strip()
            if noeud not in noeuds:
                noeuds.append(noeud)
    list_sommet={}
    for column in noeuds:
        list_sommet[column]={}
        list_sommet[column]["initiateur"]=0
        list_sommet[column]["presence"]=0
        list_sommet[column]["finisseur"]=0
        list_sommet[column]["assistant"]=0
        list_sommet[column]["initiateur_ca"]=0
        list_sommet[column]["presence_ca"]=0
        list_sommet[column]["finisseur_ca"]=0
        list_sommet[column]["assistant_ca"]=0
    for path in multichannel_paths:
        path_str = path
        nodes = path_str.split("=>")
        contribution = multichannel_paths[path]["purchased"]/len(nodes)
        contribution_ca = multichannel_paths[path]["purchase_value"]/len(nodes)
        for i in range(0,len(nodes)):
            key=nodes[i].strip()
            if i == 0:
                list_sommet[key]["initiateur"]=list_sommet[key]["initiateur"]+contribution
                list_sommet[key]["presence"]=list_sommet[key]["presence"]+contribution
                list_sommet[key]["initiateur_ca"]+=contribution_ca
                list_sommet[key]["presence_ca"]+=contribution_ca
            else :
                if i == len(nodes) - 1:
                    list_sommet[key]["finisseur"]=list_sommet[key]["finisseur"]+contribution
                    list_sommet[key]["presence"]=list_sommet[key]["presence"]+contribution
                    list_sommet[key]["finisseur_ca"]+=contribution_ca
                    list_sommet[key]["presence_ca"]+=contribution_ca
                else:
                    list_sommet[key]["assistant"]=list_sommet[key]["assistant"]+contribution
                    list_sommet[key]["presence"]=list_sommet[key]["presence"]+contribution
                    list_sommet[key]["assistant_ca"]+=contribution_ca
                    list_sommet[key]["presence_ca"]+=+contribution_ca
    return list_sommet,noeuds
