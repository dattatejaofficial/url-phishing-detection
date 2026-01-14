import sys

import re
from urllib.parse import urlsplit
import tldextract
import math
from collections import Counter

from phishingsystem.exception.exception import PhishingSystemException

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