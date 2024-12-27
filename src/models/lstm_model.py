"""
This file define LSTM model function
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense, Masking
from tensorflow.keras.preprocessing.sequence import pad_sequences
import math
import numpy as np
import math
from collections import defaultdict

def lstm_model(paths,noeuds):
    representation_binaire={} 
    binary_length = math.ceil(math.log2(len(noeuds)))  
    noeuds.insert(0, "pad_sequence")
    representation_binaire = {}
    for idx, channel in enumerate(noeuds):
        if channel == "pad_sequence":
            binary_code = [0] * binary_length
        else:
            binary_code = [int(bit) for bit in format(idx - 1, 'b').zfill(binary_length)]
        representation_binaire[channel] = binary_code 
    
    for path in paths : 
        representation_binaire_path=[]
        path_channels=path.split("=>")
        i=0
        for channel in path_channels:
            channel=channel.strip()
            representation_binaire_path.append(representation_binaire[channel])
            i+=1
            if(i>14):
                break
        for i in range(len(path_channels),15):
            representation_binaire_path.append(representation_binaire["pad_sequence"]) 
        paths[path]["binaire_representation"]=representation_binaire_path
        
    X=[]
    Y=[]
    for path in paths: 
        for i in range(0,paths[path]["purchased"]):
            Y.append(1)
            X.append(paths[path]["binaire_representation"])
        for i in range(0,paths[path]["viewed"]):
            Y.append(0)
            X.append(paths[path]["binaire_representation"])         
    X_arr = pad_sequences(X, maxlen=15, dtype='float32', padding='post', value=0.0)
    y_arr = np.array(Y)
    model = Sequential()
    model.add(Masking(mask_value=0.0, input_shape=(15, len(X_arr[0][0]))))
    model.add(LSTM(units=150, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(units=100, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1, activation='sigmoid'))
    model.compile(optimizer='RMSprop', loss='binary_crossentropy', metrics=['accuracy'])
    history = model.fit(X_arr, y_arr, epochs=6, batch_size=32)    
    return model,representation_binaire  

def preserve_ranking_and_transform(shapley_values):
    contributions = np.array(list(shapley_values.values()))
    touchpoints = list(shapley_values.keys())
    relative_contributions = {key: abs(value) for key, value in shapley_values.items()}
    max_value = max(relative_contributions.values())
    positive_scores = {key: max_value - value for key, value in relative_contributions.items()}
    total_score = sum(positive_scores.values())
    normalized_scores = {key: value / total_score for key, value in positive_scores.items()}
    return normalized_scores

def reshape_input_data(input_data, binary_length):
    if input_data.shape == (10,):  
        return input_data[np.newaxis, np.newaxis, :]
    elif input_data.shape == (15, binary_length):  
        return input_data[np.newaxis, :] 
    else:
        raise ValueError(f"Invalid input shape: {input_data.shape}")

def optimize_paths(paths, lstm_attribution, representation_binaire):
    path_to_remove=[]
    for path in paths:
        if(paths[path]["purchased"]==0):
            path_to_remove.append(path)
    for path in path_to_remove:
        del paths[path]  
    print(len(paths)) 
    binary_length = math.ceil(math.log2(len(representation_binaire)))
    for path in paths:
        channels = set()  
        nodes = path.split("=>")
        input_data = np.array(paths[path]["binaire_representation"])

        if len(input_data) > 15:
            continue
        input_data = reshape_input_data(input_data, binary_length)
        p_original = lstm_attribution.predict(input_data)
        p_total = {}
        p_total_negative={}
        for node in nodes:
            node = node.strip()

            if node not in channels:
                channels.add(node)
                new_path = []
                for i, node2 in enumerate(nodes):
                    if node2.strip() != node:
                        new_path.append(representation_binaire[node2.strip()])
                    else : 
                        new_path.append(representation_binaire["pad_sequence"])    
                    if i >= 14:  
                        break
                while len(new_path) < 15:  
                        new_path.append(representation_binaire["pad_sequence"])
                input_data = np.array(new_path)
                input_data = reshape_input_data(input_data, binary_length)
                prediction=lstm_attribution.predict(input_data)
                if( p_original - prediction>0):
                    p_total[node] = p_original - prediction  
                else : 
                    p_total[node] = 0
                    p_total_negative[node]=p_original - prediction
                    
        total = sum(p_total.values()) 
        if(total==0):
            p_total=preserve_ranking_and_transform(p_total_negative)
            total=sum(p_total.values()) 
        paths[path]["attribution"]={}
        for node in nodes:
            if(total!=0):
                paths[path]["attribution"][node] = p_total[node] / total
            else : 
                paths[path]["attribution"][node] = 0
    return paths
def attribuate_conv_to_channels(paths):
    lstm_attribution = defaultdict(lambda: {"conversions": 0, "purchase_value": 0}) 
    for path in paths:
        for noeud in paths[path]["attribution"]:
            if not np.isnan(paths[path]["attribution"][noeud]):
                lstm_attribution[noeud]["conversions"]+=paths[path]["attribution"][noeud][0][0]*paths[path]["purchased"]
                lstm_attribution[noeud]["purchase_value"]+=paths[path]["attribution"][noeud][0][0]*paths[path]["purchase_value"]
    return lstm_attribution            