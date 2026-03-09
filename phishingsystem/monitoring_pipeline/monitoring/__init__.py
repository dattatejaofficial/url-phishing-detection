import logging
from datetime import datetime, timezone
import azure.functions as func

from monitoring_utils import send_email_notification
from monitoring_trigger import run_monitoring

def main(monitoringTimer: func.TimerRequest) -> None:
    utc_now = datetime.now(timezone.utc).isoformat()
    logging.info(f'[Monitoring] Function triggered at {utc_now}')

    if monitoringTimer.past_due:
        logging.warning(f'[Monitoring] Timer is past due!')
    
    try:
        reports, decision = run_monitoring()

        if reports is None:
            logging.info(f'[Monitoring] No data or window not completed. Skipping monitoring today.')
            send_email_notification(msg = 'No data or window not completed. Skipping monitoring today.', recipient_type = 'single')
            return
        
        logging.info(f'[Monitoring] Monitoring reports generated successfully')        
        send_email_notification(msg = 'The monitoring job just ran sucessfully. Check the reports for more details.', decision = decision)

    except Exception as e:
        logging.error(f'[Monitoring] ERROR: {str(e)}', exc_info=True)
        raise e
    
    logging.info(f'[Monitoring] Function execution completed')