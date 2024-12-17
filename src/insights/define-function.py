
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


