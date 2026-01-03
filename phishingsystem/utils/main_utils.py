import sys
from phishingsystem.exception.exception import PhishingSystemException
import pandas as pd

def read_csv_file(path : str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise PhishingSystemException(e,sys)
    