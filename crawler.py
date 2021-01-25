import sys
import json
from urllib.parse import urlparse
from threading import Thread, Lock, active_count
from queue import Queue
import pprint
from time import sleep
import logging
# import os


import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

REQUESTS_TIMEOUT = 10
REQUESTS_RETRY_COUNT = 3
REQUESTS_BACKOFF_FACTOR = 1

endpoints = dict()
to_be_crawled = Queue()
already_crawled = set()
lock = Lock()


def find_links_in_html(request):
    url = request.url
    html_text = request.text
    parsed_uri = urlparse(url)
    base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    if endpoints.get(base_url, None) is None:
        endpoints[base_url] = set()

    soup = BeautifulSoup(html_text, 'html.parser')
    for link in soup.find_all('a'):
        this_link = link.get('href')
        # print(this_link)
        try:
            if not this_link.endswith('/'):
                this_link = this_link + '/'
            if this_link.startswith('/'):
                # print(this_link)
                endpoints[url].add(base_url+this_link[1:])
                if not (base_url+this_link[1:] in endpoints):
                    # print(url+this_link[1:])
                    endpoints[base_url+this_link[1:]] = set()
                    to_be_crawled.put(base_url+this_link[1:])
            elif this_link.startswith(base_url):
                endpoints[url].add(this_link)
                if not (this_link in endpoints):
                    # print(this_link)
                    endpoints[this_link] = set()
                    to_be_crawled.put(this_link)
        except Exception as e:
            print(f'Error (find_links_in_html): {str(e)}')


def crawl():
    # s = requests.Session()
    # retry = Retry(total=REQUESTS_RETRY_COUNT, backoff_factor=REQUESTS_BACKOFF_FACTOR)
    # adapter = HTTPAdapter(max_retries=retry)
    # s.mount('http://', adapter)
    # s.mount('https://', adapter)
    with requests.Session() as s:
        retry = Retry(total=REQUESTS_RETRY_COUNT, backoff_factor=REQUESTS_BACKOFF_FACTOR)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        while True:
            if not to_be_crawled.qsize()>0:
                break

            lock.acquire()
            url = to_be_crawled.get()
            if url in already_crawled:
                continue
            else:
                already_crawled.add(url)
            lock.release()
        
            try:
                r = s.get(url, timeout=REQUESTS_TIMEOUT)
                r.raise_for_status()
                # if r.status_code == 
                find_links_in_html(r)
            except Exception as e:
                print(f'Error (crawl): {str(e)}')

            sleep(1)


if __name__ == '__main__':
    try:
        url = sys.argv[1]
        num_threads = sys.argv[2]
    except Exception as e:
        # url = 'https://duckduckgo.com/'
        # url = 'https://monzo.com/'
        url = 'https://www.ismercuryinretrograde.com/'
        # url = 'https://monzo.com/i/business'
        num_threads = 1

    # logger = logging.getLogger('crawler')
    # logger.setLevel(logging.DEBUG)
    # file_handler = logging.FileHandler('crawler.log')
    # file_handler.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    print(f'URL: {str(url)}')
    print(f'Number of threads: {str(num_threads)}')

    to_be_crawled.put(url)

    crawler_threads = list()
    for i in range(int(num_threads)):
        crawler_threads.append(Thread(target=crawl))

    first_thread = True

    for thread in crawler_threads:
        thread.start()
        if first_thread:
            sleep(REQUESTS_TIMEOUT)
            first_thread = False

    # print(active_count())

    for thread in crawler_threads:
        thread.join()
    
    try:
        with open('endpoints_tree.txt', 'w') as f:
            pp = pprint.PrettyPrinter(indent=4, stream=f)
            pp.pprint(endpoints)
        with open('endpoints_list.txt', 'w') as f:
            pp = pprint.PrettyPrinter(indent=4, stream=f)
            pp.pprint(already_crawled)
    except Exception as e:
        print(f'Error (main): {str(e)}')

    exit(0)