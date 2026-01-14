import sys

import re
import requests
from urllib.parse import urlparse
import tldextract

from phishingsystem.constants import SHORT_DOMAINS
from phishingsystem.utils.url_unshortening.sqlite_app import cache_url, get_cached_url

class URLCleaner:
    def __init__(self, url):
        self.url = url
    
    def _clean_url(self, url):
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
    
    def _is_shortened(self, url: str) -> bool:
        try:
            ext = tldextract.extract(url)
            if not ext.domain or not ext.suffix:
                return False
            domain = f"{ext.domain}.{ext.suffix}"
            return domain in SHORT_DOMAINS
        except Exception:
            return False
    
    def _expand_shortened_url(self, url: str) -> str:
        cached = get_cached_url(url)
        if cached is not None:
            return cached

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            resp = requests.get(
                url,
                allow_redirects=True,
                timeout=6,
                headers=headers
            )
            expanded_url = resp.url
        except Exception:
            expanded_url = url

        cache_url(url, expanded_url)
        return expanded_url

    def _validate_url(self, url : str) -> bool:
        url_pattern = r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?"
        return bool(re.match(url_pattern,url))
    
    def _handle_missing_schema(self, url):
        scheme = urlparse(url).scheme
        if scheme == '':
            return 'http://' + url
        return url
    
    def initiate_cleaning_url(self):
        url = self._handle_missing_schema(self.url)
        url = self._clean_url(url)

        if not self._validate_url(url):
            return url
        
        if self._is_shortened(url):
            url = self._expand_shortened_url(url)
            url = self._clean_url(url)

        return url if self._validate_url(url) else self.url