import sys
import pandas as pd
import numpy as np
import yaml
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from phishingsystem.exception.exception import PhishingSystemException

def read_csv_file(path : str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise PhishingSystemException(e,sys)

def read_yaml_file(path : str) -> dict:
    try:
        with open(path,'r') as file:
            data = yaml.safe_load(file)
        return data
    
    except Exception as e:
        raise PhishingSystemException(e,sys)

def save_numpy_array(arr : np.ndarray, arr_file_path : str):
    try:
        with open(arr_file_path,'wb') as file:
            np.save(file,arr)

    except Exception as e:
        raise PhishingSystemException(e,sys)

def load_numpy_array(arr_file_path : str) -> np.ndarray:
    try:
        with open(arr_file_path,'rb') as file:
            arr = np.load(file)
        return arr

    except Exception as e:
        raise PhishingSystemException(e,sys)

def evaluate_model(y_true, y_pred) -> dict[str,float]:
    return {
        'accuracy' : accuracy_score(y_true,y_pred),
        'precision' : precision_score(y_true,y_pred),
        'recall' : recall_score(y_true,y_pred),
        'f1_score' : f1_score(y_true,y_pred)
    }