
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

def attribute_conversions_for_channels(noeuds,old_markov,new_markov,lstm_model,total_conversions):
    results={}
    for noeud in noeuds:
        noeud=noeud.strip()
        results[noeud]={}
        results[noeud]["old_markov_attribution"]=old_markov[noeud]
        results[noeud]["old_markov_attribution_conversions"]=old_markov[noeud]*total_conversions
        results[noeud]["new_markov_attrbution"]=new_markov[noeud]
        results[noeud]["new_markov_attribution_conversions"]=new_markov[noeud]*total_conversions
        results[noeud]["lstm_attribution"]=lstm_model[noeud]
        results[noeud]["lstm_attribution_conversions"]=lstm_model[noeud]*total_conversions
    return results    

def dimensions_path_by_channels(noeuds,paths):
    results={}
    for noeud in noeuds:
        total=0
        nb_touchpoint=[]
        for path in paths:    
            if (noeud in path ):
                path_original=path.split("=>")
                total+=len(path_original)
                nb_touchpoint.append(len(path_original))
                if(noeud not in results):
                    results[noeud]={}
                    results[noeud]["purchased"]=0
                    results[noeud]["viewed"]=0
                results[noeud]["purchased"]+=paths[path]["purchased"]
                results[noeud]["viewed"]+=paths[path]["viewed"]
        if(len(nb_touchpoint)!=0):
            results[noeud]["average_number_touch"]=total/len(nb_touchpoint) 
    return results            

def get_dimensions_autonomous(autonomous_paths):
    results={}
    for path in autonomous_paths:
        nodes=path.split("=>")
        key=nodes[0].strip()
        if(key not in results):
            results[key]={}
            results[key]["purchased"]=0
            results[key]["purchase_value"]=0
        results[key]["purchased"]+=autonomous_paths[path]["purchased"]
        results[key]["purchase_value"]+=autonomous_paths[path]["purchase_value"]
    return results

def attribute_purchase_value_for_channels(old_markov,new_markov,lstm_model,paths,results):
    for path in paths : 
        total_old_markov=0
        total_new_markov=0
        total_lstm=0
        nodes=path.split("=>")
        for node in nodes : 
            node=node.strip()
            total_old_markov+=old_markov[node]
            total_new_markov+=new_markov[node]
            total_lstm+=lstm_model[node]
        for node in nodes : 
            if "lstm_attrbution_purchase_value" not in results[node]:
                results[node]["lstm_attrbution_purchase_value"]=0     
                results[node]["old_markov_attrbution_purchase_value"]=0
                results[node]["new_markov_attrbution_purchase_value"]=0
            if(total_lstm!=0):    
                results[node]["lstm_attrbution_purchase_value"]+= lstm_model[node]*float(paths[path]["purchase_value"])/total_lstm   
            
            if(total_old_markov!=0) :  
                results[node]["old_markov_attrbution_purchase_value"]+=old_markov[node]*paths[path]["purchase_value"]/total_old_markov
           
            if(total_new_markov!=0):     
                results[node]["new_markov_attrbution_purchase_value"]+=new_markov[node]*paths[path]["purchase_value"]/total_new_markov
    return results        

def synergy_between_channels(paths,noeuds):
    noeuds.append("start")
    noeuds.append("end")
    matrice = {}
    for noeud in noeuds:
        values = {}
        for noeud2 in noeuds:
            values[noeud2] = 0
        matrice[noeud] = values
    for path_str in paths:
        tuples=[]
        nodes = path_str.split("=>")
        for i in range(len(nodes)):
            key=nodes[i].strip()
            if i == 0:
                matrice["start"][key]=paths[path_str]["purchased"]+matrice["start"][key]
            if i == len(nodes) - 1:
                matrice[key]["end"]=matrice[key]["end"]+ paths[path_str]["purchased"]
            else :
                if (key,nodes[i+1].strip()) not in tuples:
                    matrice[key][nodes[i+1].strip()]=matrice[key][nodes[i+1].strip()]+ paths[path_str]["purchased"]
                    tuples.append((key,nodes[i+1].strip()))
    for column in matrice :
        total = 0
        for column2 in matrice :
            total  =total+matrice[column][column2]
        total2 = 0
        for column2 in matrice :
            if total!=0:
                matrice[column][column2] = matrice[column][column2]/total
                total2 = matrice[column][column2]/total+total2
            else :
                matrice[column][column2] = 0
    return matrice    
def presence__between_channels(paths,noeuds):
    noeuds.append("start")
    noeuds.append("end")
    matrice = {}
    for noeud in noeuds:
        values = {}
        for noeud2 in noeuds:
            values[noeud2] = 0
        matrice[noeud] = values
    for path_str in paths:
        
        nodes = path_str.split("=>")
        channels=[]
        for i in range(len(nodes)):
            if nodes[i].strip() not in channels:
                channels.append(nodes[i])
        for channel in channels: 
            for channel2 in channels : 
                if(channel!=channel2):
                    matrice[channel][channel2]=paths[path_str]["purchased"]
    for column in matrice :
        total = 0
        for column2 in matrice :
            total  =total+matrice[column][column2]
        total2 = 0
        for column2 in matrice :
            if total!=0:
                matrice[column][column2] = matrice[column][column2]/total
                total2 = matrice[column][column2]/total+total2
            else :
                matrice[column][column2] = 0
    return matrice        