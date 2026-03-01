import os
import requests
import statistics

import monitoring_constants

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
MONITORING_WORKFLOW_FILE = os.getenv('MONITORING_WORKFLOW_FILE')
BRANCH = os.getenv('BRANCH')

RECALL_THRESHOLD = monitoring_constants.RECALL_THRESHOLD
SEVERE_PSI_THRESHOLD = monitoring_constants.SEVERE_PSI_THRESHOLD
PSI_THRESHOLD = monitoring_constants.PSI_THRESHOLD
VOLUME_RATIO_THRESHOLD = monitoring_constants.VOLUME_RATIO_THRESHOLD

ENABLE_DRIFT_TRIGGER = monitoring_constants.ENABLE_DRIFT_TRIGGER
ENABLE_PERFORMANCE_TRIGGER = monitoring_constants.ENABLE_PERFORMANCE_TRIGGER
ENABLE_VOLUME_TRIGGER = monitoring_constants.ENABLE_VOLUME_TRIGGER

def is_drift_significant(drift_report: dict) -> bool:
    if not drift_report:
        return False
    
    psi_values = list(drift_report.values())

    if any(psi > SEVERE_PSI_THRESHOLD for psi in psi_values):
        return True
    
    if statistics.mean(psi_values) > PSI_THRESHOLD:
        return True
    
    return False

def is_performance_degraded(performance_report: dict) -> bool:
    recall = performance_report.get('recall',1.0)
    return recall < RECALL_THRESHOLD

def is_volume_significant(volume_report: dict) -> bool:
    ratio = volume_report.get('ratio',0)
    return ratio >= VOLUME_RATIO_THRESHOLD

def should_trigger_retraining(reports: dict):
    drift_flag = False
    performance_flag = False
    volume_flag = False

    if ENABLE_DRIFT_TRIGGER:
        drift_flag = is_drift_significant(reports['drift']['feature_drift'])
    
    if ENABLE_PERFORMANCE_TRIGGER:
        performance_flag = is_performance_degraded(reports['performance'])
    
    if ENABLE_VOLUME_TRIGGER:
        volume_flag = is_volume_significant(reports['volume'])

    decision = drift_flag or volume_flag or performance_flag

    return {
        'trigger_retraining' : decision,
        'drift_trigger' : drift_flag,
        'performance_trigger' : performance_flag,
        'volume_flag' : volume_flag
    }

def trigger_github_action():
    
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise ValueError('GitHub credentials not configured')

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{MONITORING_WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization" : f"Bearer {GITHUB_TOKEN}",
        "Accept" : "application/vnd.github+json"
    }

    payload = {"ref" : BRANCH}
    response = requests.post(url, headers=headers, json=payload, timeout=15)

    if response.status_code != 204:
        raise Exception(f'GitHub Action trigger failed: {response.status_code} - {response.text}')
    
def evaluate_and_trigger(reports: dict):
    decision = should_trigger_retraining(reports)
    print('Retraining Decision: ', decision)

    if decision['trigger_retraining']:
        trigger_github_action()
        print('Retraining Triggered')
    else:
        print('Retraining not triggered')
    
    return decision