import pandas as pd
import numpy as np
import yaml

def read_yaml_file(path : str) -> dict:
    try:
        with open(path,'r') as file:
            data = yaml.safe_load(file)
        return data
    
    except Exception as e:
        raise Exception(e)

def compute_psi(ref, cur, bins=10, eps=1e-6):
    ref_hist, bin_edges = np.histogram(ref, bins)
    cur_hist, _ = np.histogram(cur, bin_edges)

    ref_pct = ref_hist / max(len(ref),1)
    cur_pct = cur_hist / max(len(cur),1)

    return float(np.sum((cur_pct - ref_pct) * np.log((cur_pct + eps) / (ref_pct + eps))))

def compute_drift_report(reference_df : pd.DataFrame, current_df : pd.DataFrame, active_features):
    try:
        report = {}

        for feature in active_features:
            report[feature] = compute_psi(reference_df[feature].values, current_df[feature].values)
        
        return report
    
    except Exception as e:
        raise Exception(e)

def compute_performance_metrics(df: pd.DataFrame):
    tp = ((df.y_true == 1) & (df.y_pred == 1)).sum()
    fp = ((df.y_true == 0) & (df.y_pred == 1)).sum()
    tn = ((df.y_true == 0) & (df.y_pred == 0)).sum()
    fn = ((df.y_true == 1) & (df.y_pred == 0)).sum()

    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / max(tp + fp,1)
    recall = tp / max(tp + fn, 1)

    return {
        "accuracy" : accuracy,
        "precision" : precision,
        "recall" : recall,
        "sample_count" : len(df)
    }

def compute_data_volume(new_rows, last_training_rows):
    try:
        return {
            "new_data_rows" : new_rows,
            "last_training_rows" : last_training_rows,
            "ratio" : round(new_rows / max(last_training_rows, 1), 3)
        }
    
    except Exception as e:
        raise Exception(e)