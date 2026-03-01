import logging
import azure.functions as func
from datetime import datetime, timezone

from monitoring_trigger import run_monitoring
from retraining_controller.controller import evaluate_and_trigger

def main(monitoringTimer: func.TimerRequest) -> None:
    utc_now = datetime.now(timezone.utc).isoformat()
    logging.info(f'[Monitoring] Function triggered at {utc_now}')

    if monitoringTimer.past_due:
        logging.warning(f'[Monitoring] Timer is past due!')
    
    try:
        reports = run_monitoring()

        if reports is None:
            logging.info(f'[Monitoring] No data found. Skipping evaluation')
            return
        
        logging.info(f'[Monitoring] Monitoring reports generated successfully')

        decision = evaluate_and_trigger(reports)
        logging.info(f'[Monitoring] Retraining decision: {decision}')

    except Exception as e:
        logging.error(f'[Monitoring] ERROR: {str(e)}', exc_info=True)
        raise e
    
    logging.info(f'[Monitoring] Function execution completed')