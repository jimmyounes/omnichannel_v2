"""
This file define LSTM model function
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense, Masking
from tensorflow.keras.preprocessing.sequence import pad_sequences
import math

def lstm_model(paths,noeuds):
    path_to_remove=[]
    for path in paths:
        if(paths[path]["purchased"]<1):
            path_to_remove.append(path)
    for path in path_to_remove:
        del paths[path]  
             
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
    history = model.fit(X_arr, y_arr, epochs=9, batch_size=32)    
    probabilite_paths={}
    for path in paths:
        input_data = np.array(paths[path]["binaire_representation"])
        if(len(paths[path]["binaire_representation"])>15):
            continue
        if input_data.shape == (10,):  
            input_data = input_data[np.newaxis, np.newaxis, :] 
        elif input_data.shape == (15, binary_length):  
            input_data = input_data[np.newaxis, :] 
        else:
            raise ValueError(f"Invalid input shape: {input_data.shape}")
        probabilite_paths[path] = model.predict(input_data)  
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
                if (noeud_present==False and path_str in probabilite_paths):
                    sum=sum+probabilite_paths[path_str].item()
            re=sum/all_path_prob
            removal_effect[noeud] = 1-re 
    total_removal_effect = 0
    for noeud in removal_effect:
        if(noeud!="Direct"):
            total_removal_effect = total_removal_effect+removal_effect[noeud] 
    normalized_re={}
    for noeud in removal_effect:
        if(noeud!="Direct"):
            normalized_re[noeud] = removal_effect[noeud]/total_removal_effect
    all=0
    for noeud in normalized_re:
        normalized_re[noeud]=normalized_re[noeud][0][0]
    return normalized_re