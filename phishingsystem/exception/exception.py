import sys
from phishingsystem.logging import logger

class PhishingSystemException(Exception):
    def __init__(self, error_message, error_details : sys):
        self.error_message = error_message
        _, _, exc_tb = error_details.exc_info()

        self.line_no = exc_tb.tb_lineno
        self.file_name = exc_tb.tb_frame.f_code.co_filename

    def __str__(self):
        return f"Error occured in script name [{self.file_name}] line number [{self.line_no}] error message [{self.error_message}]"

if __name__ == '__main__':
    try:
        logger.logging.info('Enter the try block')
        a = 1 / 0
        print('This will not be printed',a)
    except Exception as e:
        logger.logging.error('Raised an exception')
        raise PhishingSystemException(e,sys)