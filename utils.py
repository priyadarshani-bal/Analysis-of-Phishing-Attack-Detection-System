import re
import urllib.parse

def extract_features(url):
    parsed = urllib.parse.urlparse(url)

    return [
        len(url),
        1 if url.startswith("https") else 0,
        url.count('.'),
        len(parsed.netloc),
        1 if re.search(r'@', url) else 0,
        1 if '-' in parsed.netloc else 0,
        1 if re.search(r'login|verify|bank|secure|update', url, re.I) else 0
    ]

def extract_email_features(text):
    return [
        len(text),
        1 if re.search(r'urgent|immediately', text, re.I) else 0,
        1 if re.search(r'http[s]?://', text) else 0,
        1 if re.search(r'bank|login|account|password', text, re.I) else 0
    ]