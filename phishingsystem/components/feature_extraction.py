import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import FeatureExtractionConfig
from phishingsystem.entity.artifact_entity import DataPreparationArtifact, FeatureExtractionArtifact

from phishingsystem.utils.main_utils import read_csv_file

import re
import pandas as pd
from urllib.parse import urlsplit
import tldextract
import math
from collections import Counter

class URLFeaturesExtraction:
    def __init__(self, url : str):
        self.url = url
        self._parse_url()
    
    def _parse_url(self):
        try:
            result = urlsplit(self.url)
            self.protocol = result.scheme
            self.domain = result.netloc
            self.path = result.path
            self.query = result.query

            ext = tldextract.extract(self.url)
            self.subdomain = ext.subdomain
            self.sld = ext.domain
            self.tld = ext.suffix
        
        except Exception:
            self.protocol = ""
            self.domain = ""            
            self.path = ""
            self.query = ""
            self.subdomain = ""
            self.sld = ""
            self.tld = ""
    
    def _calculate_depth(self) -> int:
        try:
            protocol_re = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*:(//)?')
            url = protocol_re.sub('',self.url)
            parts = url.split('/',1)

            if len(parts) == 1:
                return 0
            
            path = parts[1]
            depth = sum(1 for seg in path.split('/') if seg)
            return depth

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _shannon_entropy(self, text : str) -> float:
        try:
            counts = Counter(text)
            length = len(text)
            return -sum((count / length) * math.log2(count / length) for count in counts.values())

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _count_tokens(self, domain : str, path : str) -> tuple[int, int]:
        try:
            domain_tokens = domain.replace('.',' ').replace('-',' ').replace('_',' ').split()
            path_tokens = path.replace('.',' ').replace('-',' ').replace('_',' ').split()

            return len(domain_tokens), len(path_tokens)
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _avg_token_length(self) -> float:
        try:
            protocol_re = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',re.IGNORECASE)
            split_re = re.compile(r'[./?=\-_&:%]+')

            url = protocol_re.sub('',self.url)
            tokens = split_re.split(url)
            tokens = [t for t in tokens if t]

            if not tokens:
                return 0
            return sum(len(t) for t in tokens) / len(tokens)
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def extract_features(self) -> dict[str, float]:
        try:
            features = {}
            features['has_https'] = int(self.protocol == 'https')

            # Length features
            features['url_len'] = len(self.url)
            features['domain_len'] = len(self.domain)
            features['path_len'] = len(self.path)
            features['query_len'] = len(self.query)
            features['url_depth'] = self._calculate_depth()
            
            # Domain & SLD features
            features['subdomain_count'] = len(self.subdomain.split('.')) if self.subdomain else 0
            features['tld_len'] = len(self.tld)
            features['sld_len'] = len(self.sld)
            features['sld_has_digit'] = int(bool(re.search(r'\d',self.sld)))
            features['sld_has_hyphen'] = int('-' in self.sld)

            # Character features
            features['dot_count_domain'] = self.domain.count('.')
            features['hyphen_count_domain_path'] = (self.domain + self.path).count('-')
            features['underscore_count_path_query'] = (self.path + self.query).count('_')
            features['slash_count'] = self.url.count('/')
            features['digit_count'] = len(re.findall(r'\d',self.url))
            features['alphabet_count'] = len(re.findall(r'[a-zA-Z]',self.url))
            features['spl_char_count'] = len(re.findall(r'[^a-zA-Z0-9]',self.url))

            # Entropy features
            features['url_entropy'] = self._shannon_entropy(self.url)
            features['domain_entropy'] = self._shannon_entropy(self.domain)
            features['sld_entropy'] = self._shannon_entropy(self.sld)
            features['path_entropy'] = self._shannon_entropy(self.path)

            # Token features
            domain_tokens_count, path_tokens_count = self._count_tokens(self.domain, self.path)
            features['domain_token_count'] = domain_tokens_count
            features['path_token_count'] = path_tokens_count
            features['avg_token_length'] = self._avg_token_length()

            return features

        except Exception as e:
            raise PhishingSystemException(e,sys)

class FeatureExtraction:
    def __init__(self, data_preparation_artifact : DataPreparationArtifact, feature_extraction_config : FeatureExtractionConfig):
        self.data_preparation_artifact = data_preparation_artifact
        self.feature_extraction_config = feature_extraction_config
    
    def initiate_feature_extraction(self):
        try:
            logging.info('Initiating Feature Extraction')

            processed_data = read_csv_file(self.data_preparation_artifact.processed_data_path)
            url_col = self.data_preparation_artifact.processed_column_name

            features_dict = processed_data[url_col].apply(lambda url: URLFeaturesExtraction(url).extract_features())
            logging.info('Extracted features from the URLs')

            features_df = pd.DataFrame(features_dict.tolist())
            target_col = self.data_preparation_artifact.target_column_name
            features_df[target_col] = processed_data[target_col]

            features_data_path = self.feature_extraction_config.features_data_path
            dir_path = os.path.dirname(features_data_path)
            os.makedirs(dir_path, exist_ok=True)

            features_df = features_df.drop_duplicates(ignore_index=True)
            features_df.to_csv(features_data_path,index=False,header=True)
            logging.info('Saved the features data')

            feature_extraction_artifact = FeatureExtractionArtifact(
                features_data_path = features_data_path
            )

            logging.info('Completed feature extraction')
            return feature_extraction_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)