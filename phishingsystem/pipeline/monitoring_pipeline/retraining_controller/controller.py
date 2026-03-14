import os
import requests
import statistics
from datetime import datetime
from zoneinfo import ZoneInfo

from monitoring_constants import *

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

def is_drift_significant(drift_report: dict) -> bool:
    if not drift_report:
        return False
    
    psi_values = list(drift_report.get('drift_report', {}).get('feature_drift', {}).values())
    
    if not psi_values:
        return False

    if any(psi > SEVERE_PSI_THRESHOLD for psi in psi_values):
        return True
    
    if statistics.mean(psi_values) > PSI_THRESHOLD:
        return True
    
    return False

def is_performance_degraded(performance_report: dict) -> bool:
    if not performance_report:
        return False
    
    recall = performance_report.get('performance_report',{}).get('recall',1.0)
    return recall < RECALL_THRESHOLD

def is_volume_significant(volume_report: dict) -> bool:
    if not volume_report:
        return False
    
    ratio = volume_report.get('volume_report', {}).get('ratio', 0)
    return ratio >= VOLUME_RATIO_THRESHOLD

def should_trigger_retraining(reports: dict):
    drift_flag = False
    performance_flag = False
    volume_flag = False

    if ENABLE_DRIFT_TRIGGER:
        drift_flag = is_drift_significant(reports.get('drift', {}))
    
    if ENABLE_PERFORMANCE_TRIGGER:
        performance_flag = is_performance_degraded(reports.get('performance', {}))
    
    if ENABLE_VOLUME_TRIGGER:
        volume_flag = is_volume_significant(reports.get('volume', {}))

    decision = drift_flag or volume_flag or performance_flag

    return {
        'drift trigger' : drift_flag,
        'performance trigger' : performance_flag,
        'volume flag' : volume_flag,
        'trigger retraining' : decision,
        "computed at" : datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y %H:%M:%S")
    }

def trigger_github_action():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise ValueError('GitHub credentials not configured')

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{RETRAINING_WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization" : f"Bearer {GITHUB_TOKEN}",
        "Accept" : "application/vnd.github+json"
    }

    payload = {"ref" : GITHUB_BRANCH}
    response = requests.post(url, headers=headers, json=payload, timeout=15)

    if response.status_code != 204:
        raise Exception(f'GitHub Action trigger failed: {response.status_code} - {response.text}')
    
def evaluate_and_trigger(reports: dict):
    decision = should_trigger_retraining(reports)
    print('Retraining Decision: ', decision)

    if decision['trigger retraining']:
        trigger_github_action()
        print('Retraining Triggered')
    else:
        print('Retraining not triggered')
    
    return decision