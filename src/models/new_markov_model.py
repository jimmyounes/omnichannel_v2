"""
This file defines new process of markov chain that take in count
 viewed and conversions dimension in the model
"""

def new_process_omnichannel(paths,noeuds):
    """
    Return Results of channel attribution of new process omnichannel 
    """
    matrice = {}
    noeuds.append("start")
    noeuds.append("end")
    for noeud in noeuds:
        values = {}
        for noeud2 in noeuds:
            values[noeud2] = 0
        matrice[noeud] = values
    for path_str in paths:
        nodes = path_str.split("=>")
        for i in range(len(nodes)):
            key=nodes[i].strip()
            if i == 0:
                matrice["start"][key]=paths[path_str]["viewed"]+matrice["start"][key]
            if i == len(nodes) - 1:
                matrice[key]["end"]=matrice[key]["end"]+ paths[path_str]["purchased"]
            else :
                matrice[key][nodes[i+1].strip()]=matrice[key][nodes[i+1].strip()]+ paths[path_str]["viewed"]
    for column in matrice :
        total = 0
        for column2 in matrice :
            total  =total+matrice[column][column2]
        total2 = 0
        for column2 in matrice :
            if  total!=0:
                matrice[column][column2] = matrice[column][column2]/total
                total2 = matrice[column][column2]/total+total2
            else :
                matrice[column][column2] = 0
    probabilite_paths={}
    for path_str in paths:
        probabilite=1
        nodes = path_str.split("=>")
        for i in range(len(nodes)):
            key=nodes[i].strip()
            if i == 0:
                probabilite=probabilite*matrice["start"][key]
            if i == len(nodes) - 1:
                probabilite=probabilite*matrice[key]["end"]
            else :
                probabilite=probabilite*matrice[key][nodes[i+1].strip()]
        probabilite_paths[path_str]=probabilite

    all_path_prob=0
    for path in probabilite_paths:
        all_path_prob=all_path_prob+probabilite_paths[path]
    removal_effect = {}
    for noeud in noeuds:
        if(noeud!="start" and noeud!="end"):
            sum = 0
            for path_str in paths:
                noeud_present=False
                nodes = path_str.split("=>")
                for i in range(len(nodes)):
                    key=nodes[i].strip()
                    if key==noeud:
                        noeud_present=True
                        break
                if noeud_present==False:
                    sum=sum+probabilite_paths[path_str]
            re=sum/all_path_prob
            removal_effect[noeud] = 1-re
    total_removal_effect = 0
    for noeud in removal_effect:
        if noeud!="Direct":
            total_removal_effect = total_removal_effect+removal_effect[noeud]
    normalized_re={}
    for noeud in removal_effect:
            normalized_re[noeud] = removal_effect[noeud]/total_removal_effect
    return normalized_re  
