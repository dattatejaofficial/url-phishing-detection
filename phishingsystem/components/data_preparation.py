import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

import pandas as pd
import re
from urllib.parse import urlparse
import tldextract
import aiohttp
import asyncio

from phishingsystem.constants import SHORT_DOMAINS
from phishingsystem.utils.main_utils import read_csv_file
from phishingsystem.utils.url_shortening.sqlite_app import init_cache, get_cached_url, cache_url

from phishingsystem.entity.config_entity import DataPreparationConfig
from phishingsystem.entity.artifact_entity import DataPreparationArtifact

class DataPreparation:
    def __init__(self, data_preparation_config : DataPreparationConfig):
        self.preparation_config = data_preparation_config
    
    def _clean_url(self, url : str) -> str:
        try:
            # 1. Remove zero-width characters
            zero_width = r'[\u200B\u200C\u200D\u2060\uFEFF]'
            url = re.sub(zero_width,'',url)

            # 2. Remove all ASCII control characters (0-31 and 127)
            url = re.sub(r'[\x00-\x1F\x7F]','',url)

            # 3. Remove all non-printable unicode control symbols
            unicode_controls = r'[\u202A-\u202E\u2066-\u2069]'
            url = re.sub(unicode_controls,'',url)

            # 4. Remove soft hyphens
            url = url.replace('\u00AD','').replace('\ufeff','')

            # 5. Normalize accidental triple slashes
            url = re.sub(r':\/\/\/+','://',url)

            # 6. Fix missing colon after https (caused by invisible characters earlier)
            url = re.sub(r'^(https?)(\/\/)', r'\1://', url)

            # 7. Remove spaces around colon in scheme (malformed URLs)
            url = re.sub(r'^(https?)\s*:\s*\/\/', r'\1://', url)

            # 8. Remove trailing slashes
            url = url.rstrip('/')

            return url.strip()

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _is_shortened(self, url : str) -> bool:
        try:
            ext = tldextract.extract(url)
            domain = f'{ext.domain}.{ext.suffix}'
            return domain in SHORT_DOMAINS

        except Exception as e:
            raise PhishingSystemException(e,sys)

    async def _expand_async(self, session, url):
        cached = get_cached_url(url)

        if cached is not None:
            return url, cached
        
        try:
            headers = {
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            }
            async with session.get(
                url,
                allow_redirects = True,
                timeout = 6,
                headers = headers
            ) as resp:
                expanded_url = str(resp.url)
        except Exception:
            expanded_url = url

        cache_url(url, expanded_url)
        return url,expanded_url

    async def _process_async(self, urls):
        results = {}
        async with aiohttp.ClientSession() as session:
            tasks = [self._expand_async(session, url) for url in urls]
            for fut in asyncio.as_completed(tasks):
                original, expanded = await fut
                results[original] = expanded
            return results
    
    def _run_async(self, coro):
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(coro)
        except RuntimeError:
            return asyncio.run(coro)
    
    def _validate_url(self, url : str) -> bool:
        try:
            url_pattern = r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?"
            return bool(re.match(url_pattern,url))

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _handling_missing_schema(self, url : str) -> str:
        try:
            scheme = urlparse(url).scheme
            if scheme == '':
                return 'http://' + url
            return url

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _expand_shortened_urls(self, df: pd.DataFrame, url_column : str) -> pd.DataFrame:
        try:
            shortened_mask = df[url_column].apply(self._is_shortened)
            shortened_urls = df.loc[shortened_mask, url_column].unique()

            if len(shortened_urls) == 0:
                df[self.preparation_config.processed_url_column_name] = df[url_column]
                return df
            
            results = self._run_async(self._process_async(shortened_urls))

            df[self.preparation_config.processed_url_column_name] = df[url_column].apply(lambda x: results.get(x,x))
            return df
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _encode_label(self, df : pd.DataFrame, label_column : str) -> pd.DataFrame:
        try:
            df[label_column] = df[label_column].map(lambda x: 1 if x == 'phishing' else 0)
            return df
    
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def initiate_data_preparation(self) -> DataPreparationArtifact:
        try:
            logging.info('Initiating Data Preparation stage')
            init_cache()
            df = read_csv_file(self.preparation_config.raw_data_path)

            original_url_col_name = self.preparation_config.original_url_column_name
            processed_url_col_name = self.preparation_config.processed_url_column_name
            target_col_name = self.preparation_config.target_column_name

            # Handle URL with missing schema
            df[original_url_col_name] = df[original_url_col_name].apply(self._handling_missing_schema)
            logging.info('Handled missing schema of URLs in the raw dataset')

            # Clean URLs
            df[original_url_col_name] = df[original_url_col_name].apply(self._clean_url)
            logging.info('Cleaned URLs in the raw dataset')

            # Expand shortened URLs
            df = self._expand_shortened_urls(df, original_url_col_name)
            logging.info('Expanded Shortened URLs in the raw dataset')

            # Clean the expanded URLs
            df[processed_url_col_name] = df[processed_url_col_name].apply(self._clean_url)
            logging.info('Cleaned expanded URLs in the raw dataset')

            # Validating URLs and removing invalid URLs
            df = df[df[processed_url_col_name].apply(self._validate_url)]
            logging.info('Validated URLs in the raw dataset')

            # Remove null values
            df = df.dropna(subset=[processed_url_col_name])
            logging.info('Removed null values')

            # Remove duplicates
            df = df.drop_duplicates(subset=[processed_url_col_name])
            logging.info('Removed duplicates')

            # Encode label
            df = self._encode_label(df, target_col_name)
            logging.info('Encoded labels in the raw dataset')

            # Save the processed data
            processed_data_path = self.preparation_config.processed_data_path
            dir_path = os.path.dirname(processed_data_path)
            os.makedirs(dir_path, exist_ok=True)
            df.to_csv(processed_data_path, index=False, header=True)
            logging.info('Saved the processed data')

            data_preparation_artifact = DataPreparationArtifact(
                processed_data_path = processed_data_path,
                processed_column_name = processed_url_col_name,
                target_column_name = target_col_name
            )
            logging.info('Completed Data Preparation')
            return data_preparation_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)