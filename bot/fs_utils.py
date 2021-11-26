import magic
import re
import requests
import bs4
import os

CRYPT = os.environ.get('CRYPT', None)
PHPSESSID = os.environ.get('PHPSESSID', None)

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

def is_gdrive_link(url: str):
    return bool("drive.google.com" in url)

def is_gdtot_link(url: str):
    url = re.match(r'https?://.*.gdtot.\S+', url)
    return bool(url)

def gdtot(url: str) -> str:
    """ Gdtot google drive link generator
    By https://github.com/oxosec """
    
    if CRYPT is not None:
        cookies = {"PHPSESSID": PHPSESSID, "crypt": CRYPT}
    else:
        return None

    headers = {'upgrade-insecure-requests': '1',
               'save-data': 'on',
               'user-agent': 'Mozilla/5.0 (Linux; Android 10; Redmi 8A Dual) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36',
               'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
               'sec-fetch-site': 'same-origin',
               'sec-fetch-mode': 'navigate',
               'sec-fetch-dest': 'document',
               'referer': '',
               'prefetchAd_3621940': 'true',
               'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7'}
    r1 = requests.get(url, headers=headers, cookies=cookies).content
    s1 = bs4.BeautifulSoup(r1, 'html.parser').find('button', id="down").get('onclick').split("'")[1]
    headers['referer'] = url
    s2 = bs4.BeautifulSoup(requests.get(s1, headers=headers, cookies=cookies).content, 'html.parser').find('meta').get('content').split('=',1)[1]
    headers['referer'] = s1
    s3 = bs4.BeautifulSoup(requests.get(s2, headers=headers, cookies=cookies).content, 'html.parser').find('div', align="center")
    if s3 is None:
        s3 = bs4.BeautifulSoup(requests.get(s2, headers=headers, cookies=cookies).content, 'html.parser')
        status = s3.find('h4').text
        return None
    else:
        gdlink = s3.find('a', class_="btn btn-outline-light btn-user font-weight-bold").get('href')
        return gdlink

def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type if mime_type else "text/plain"
    return mime_type


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'
