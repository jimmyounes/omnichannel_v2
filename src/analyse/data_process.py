"""""
File that processes retrieved Google Analytics data to construct conversion paths 

"""
import itertools
from src.analyse.utils.script import *
from collections import defaultdict



def get_users_path(data):
    """"
    This function enables mapping out the user's journey path. 
    """
    users_dict = defaultdict(list)  
    
    for result in data["rows"]:
        item = result['dimensionValues']
        user_id = item[3]["value"]
        users_dict[user_id].append({
            "date": item[0]["value"],
            "event": item[1]["value"],
            "source": item[2]["value"],
            "purchase_value": result["metricValues"][0]["value"]
        })
    return users_dict    

def build_journey_paths(users_journey):
    """""
    Builds journey path with dimensions viewed and purchased and average time to convert 
    """
    for user in users_journey:
        users_journey[user].sort(key=lambda x: x['date'])
    
    paths = {}

    def initialize_path(path):
        """Initialize a dictionary for a new path."""
        return {
            "purchased": 0,
            "viewed": 0,
            "time_to_purchase": [],
            "purchase_value": 0.0
        }

    for user, journey in users_journey.items():
        path = []
        date1 = None

        for touchpoint in journey:
            source = touchpoint["source"].strip()
            if not path: 
                date1 = touchpoint["date"]
            path.append(source)
            if touchpoint["event"] == "purchase":
                date2 = touchpoint["date"]
                time_diff = difference_date(date1, date2)
                full_path = "=>".join(path)

                if full_path not in paths:
                    paths[full_path] = initialize_path(full_path)
                paths[full_path]["purchased"] += 1
                paths[full_path]["purchase_value"] += float(touchpoint["purchase_value"])
                paths[full_path]["time_to_purchase"].append(time_diff)
                path = []  
                date1 = None
        if path:
            full_path = "=>".join(path)
            if full_path not in paths:
                paths[full_path] = initialize_path(full_path)
            
            paths[full_path]["viewed"] += 1
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
                path_without_direct[path]["time_to_purchase"]
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
                    autonomous_paths[path]["time_to_purchase"]
                else:
                    autonomous_paths[path]["purchased"]+=paths[original_path]["purchased"]
                    autonomous_paths[path]["purchase_value"]+=paths[original_path]["purchase_value"]
                    autonomous_paths[path]["viewed"]+=paths[original_path]["viewed"]
                    autonomous_paths[path]["time_to_purchase"] = list(itertools.chain(
                        paths[original_path]["time_to_purchase"],
                        autonomous_paths[path]["time_to_purchase"]))

    for path in path_without_direct:
        if "time_to_purchase" in path_without_direct[path] and len(path_without_direct[path]["time_to_purchase"])!=0:
            avg_time_to_purchase = sum(path_without_direct[path]["time_to_purchase"]) /len(path_without_direct[path]["time_to_purchase"])
        else:
            avg_time_to_purchase = None
        path_without_direct[path]["avg_time_to_purchase"]=avg_time_to_purchase
    for path in autonomous_paths:
        if "time_to_purchase" in autonomous_paths[path] and len(autonomous_paths[path]["time_to_purchase"])!=0:
            avg_time_to_purchase = sum(autonomous_paths[path]["time_to_purchase"]) /len(autonomous_paths[path]["time_to_purchase"])
        else:
            avg_time_to_purchase = None
        autonomous_paths[path]["avg_time_to_purchase"]=avg_time_to_purchase    
    return path_without_direct,autonomous_paths

def assembly_purchases_by_date(users_dict):
    """""
    Assembly purchases by date
    """
    for user in users_dict:
        users_dict[user].sort(key=lambda x: x['date'])
    date_autonomous_results = defaultdict(lambda: defaultdict(lambda: {"purchased": 0, "purchase_value": 0}))
    date_results = defaultdict(lambda: defaultdict(lambda: {"purchased": 0, "purchase_value": 0}))
    for user, touchpoints in users_dict.items():
        path = []
        for touchpoint in touchpoints:
            source = touchpoint["source"].strip()
            path.append(source)
            if touchpoint["event"] == "purchase":
                date2 = transform_date(touchpoint["date"])
                path_str = "=>".join(path)
                if len(set(path)) == 1:  
                    result_dict = date_autonomous_results
                else:
                    result_dict = date_results
                result_dict[date2][path_str]["purchased"] += 1
                result_dict[date2][path_str]["purchase_value"] += float(touchpoint["purchase_value"])
                path = []
    return dict(date_results), dict(date_autonomous_results)
def paths_cleaning_by_date(date_results,date_autnomous_results):
    path_without_direct={}
    for date in date_results:
        path_without_direct[date]={}
        for path in date_results[date]:
            original_path=path

            path=path.replace("=>(direct) / (none)=>","=>")
            path=path.replace("(direct) / (none)=>","")
            path=path.replace("=>(direct) / (none)","")
            if path!="" and  path_is_autonomous(path)==False:
                if(date not in path_without_direct):
                    path_without_direct[date]={}
                if path not in path_without_direct[date]:
                    path_without_direct[date][path]=date_results[date][original_path]
                else:
                    path_without_direct[date][path]["purchased"]+=date_results[date][original_path]["purchased"]
                    path_without_direct[date][path]["purchase_value"]+=date_results[date][original_path]["purchase_value"]
            else:
                if(path_is_autonomous(path)):
                    
                    if(date not in date_autnomous_results):
                        date_autnomous_results[date]={}
                    if path not in date_autnomous_results[date]:
                        date_autnomous_results[date][path]=date_results[date][original_path]
                    else:
                        
                        date_autnomous_results[date][path]["purchased"]+=date_results[date][original_path]["purchased"]
                        date_autnomous_results[date][path]["purchase_value"]+=date_results[date][original_path]["purchase_value"]
    return path_without_direct,date_autnomous_results 

def analyse_summary(multifunnels_paths,autonomous_paths,noeuds):
    total_conversions=0
    total_purchase_value=0
    number_of_paths=0
    conversions_multichannel_paths=0
    purchase_value_multichannel_paths=0
    conversions_autonomous_paths=0
    purchase_value_autonomous_paths=0
    for path in multifunnels_paths:
        conversions_multichannel_paths+=multifunnels_paths[path]["purchased"]
        total_conversions+=multifunnels_paths[path]["purchased"]
        number_of_paths+=1
        total_purchase_value+=multifunnels_paths[path]["purchase_value"]
        purchase_value_multichannel_paths+=multifunnels_paths[path]["purchase_value"]
    for path in autonomous_paths : 
        conversions_autonomous_paths+=autonomous_paths[path]["purchased"]
        total_conversions+=autonomous_paths[path]["purchased"]
        number_of_paths+=1
        total_purchase_value+=autonomous_paths[path]["purchase_value"]
        purchase_value_autonomous_paths+=autonomous_paths[path]["purchase_value"]

    results={
        "total_conversions":total_conversions,
        "turnover" : total_purchase_value , 
        "number_of_paths" : number_of_paths,
        "nb_multichannel_path" : len(multifunnels_paths),
        "nb_autonomous_path" : len(autonomous_paths),
        "number_of_channels" : len(noeuds),
        "multichannels_conversions" : conversions_multichannel_paths,
        "multichannels_purchase_value" : purchase_value_multichannel_paths,
        "autonomous_conversions" : conversions_autonomous_paths,
        "autonomous_purchase_value" : purchase_value_autonomous_paths
    }
    return results
def channels_roles(multichannel_paths):
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

def deleting_first_week(users_journey,date_list):
    if len(date_list) < 8:
        raise ValueError("date_list must have at least 8 elements")
    for user in users_journey:
        users_journey[user] = sorted(users_journey[user], key=lambda x: x['date'])
    
    users_to_delete = []
    
    for user, journey in users_journey.items():
        j = -1
        for i, touchpoint in enumerate(journey):
            if touchpoint["event"] == "purchase":
                date2 = transform_date(touchpoint["date"])
                if date_list[7] > date2:
                    j = i
        if  j + 1 == len(journey):
            users_to_delete.append(user)
        else:
            users_journey[user] = journey[j + 1:]
    for user in users_to_delete:
        del users_journey[user]
    
    return users_journey  


