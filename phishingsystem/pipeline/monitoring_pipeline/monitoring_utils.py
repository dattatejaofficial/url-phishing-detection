import os
import pandas as pd
import numpy as np
import yaml
from azure.communication.email import EmailClient

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

def compute_data_volume(new_rows, last_training_rows):
    try:
        return {
            "new_data_rows" : new_rows,
            "last_training_rows" : last_training_rows,
            "ratio" : round(new_rows / max(last_training_rows, 1), 3)
        }
    
    except Exception as e:
        raise Exception(e)

def send_email_notification(msg, decision = None, recipient_type='all'):
    try:
        connection_string = os.getenv('COMMUNICATION_SERVICES_CONNECTION_STRING')
        sender_email = os.getenv('SENDER_EMAIL')
        
        recipients = []
        if recipient_type == "all":
            recipients = [
                os.getenv('RECIPIENT1_EMAIL'),
                os.getenv('RECIPIENT2_EMAIL'),
                os.getenv('RECIPIENT3_EMAIL'),
                os.getenv('RECIPIENT4_EMAIL')
            ]
        elif recipient_type == 'single':
            recipients = [os.getenv('RECIPIENT1_EMAIL')]

        client = EmailClient.from_connection_string(connection_string)

        html_text = ""        
        if decision:
            rows = ""

            for key, value in decision.items():
                key_display = key.title()

                if key == "trigger retraining":
                    value_html = f"<b>{value}</b>"
                else:
                    value_html = value
                
                rows += f"<tr><td>{key_display}</td><td>{value_html}</td></tr>"
            
            html_text = f"""
            <h2>Phishguard Monitoring Report</h2>

            <table border="1" cellpadding="6" cellspacing="0">
                <tr>
                    <th>Metric</th>
                    <th>Status</th>
                </tr>
                {rows}
            </table>
            """
        message = {
            'senderAddress' : sender_email,
            'recipients' : {
                'to' : [{'address': r} for r in recipients]
            },
            'content' : {
                'subject' : 'Phishguard - Daily Monitoring report',
                'html' : html_text if decision else msg
            }
        }

        poller = client.begin_send(message)
        result = poller.result()

        return result
    
    except Exception as e:
        raise Exception(e)