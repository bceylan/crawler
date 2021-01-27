from urllib.parse import urlsplit
from threading import Thread, Lock
from queue import Queue
import pprint
from time import sleep
import logging

import click
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from validator_collection import checkers

REQUESTS_TIMEOUT = 3
REQUESTS_RETRY_COUNT = 3
REQUESTS_BACKOFF_FACTOR = 1

endpoints = dict()
to_crawl = Queue()
already_crawled = set()
crawl_set = set()
lock = Lock()


def insert_url_into_endpoints_dict(url, url2=None):
    if url not in endpoints:
        endpoints[url] = set()
    if url2 is not None:
        endpoints[url].add(url2)


def insert_url_into_crawl_target_set(url):
    if url not in crawl_set:
        crawl_set.add(url)
        to_crawl.put(url)


def is_link_interesting(this_link, base_url, url, logger):
    if this_link is None:
        return
    try:
        if this_link.startswith('/'):
            insert_url_into_endpoints_dict(url, base_url+this_link[1:])
            insert_url_into_crawl_target_set(base_url+this_link[1:])
        elif this_link.startswith(base_url):
            insert_url_into_endpoints_dict(url, this_link)
            insert_url_into_crawl_target_set(this_link)
        # else:
        #     logger.warning(f'Out-of-scope link: {str(this_link)}')
    except Exception as e:
        logger.error(f'(is_link_interesting): {str(e)}. Link: \
                     {str(this_link)}')


def find_links_in_html(request, base_url, all_links, logger):
    url = request.url
    html_text = request.text
    parsed_url = urlsplit(url)

    if not parsed_url.geturl().startswith(base_url):
        return

    insert_url_into_endpoints_dict(parsed_url.geturl())

    soup = BeautifulSoup(html_text, 'html.parser')
    if all_links:
        for link in soup.find_all(href=True):
            this_link = link.get('href')
            is_link_interesting(this_link, base_url, url, logger)
    else:
        for link in soup.find_all('a'):
            this_link = link.get('href')
            is_link_interesting(this_link, base_url, url, logger)


def crawl(base_url, all_links, logger):
    logger.debug(f'Starting thread with base url: {base_url}')
    # Start by opening a session.
    with requests.Session() as s:
        # Set request retry policy.
        retry = Retry(total=REQUESTS_RETRY_COUNT,
                      backoff_factor=REQUESTS_BACKOFF_FACTOR)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        while True:
            # Stop thread execution if there's no crawl target left.
            if not to_crawl.qsize() > 0:
                break

            # Acquire a lock to prevent multiple threads doing the same job.
            if lock.acquire(timeout=5):
                url = to_crawl.get()
                # Check whether the url was crawled before.
                if url in already_crawled:
                    lock.release()
                    continue
                else:
                    already_crawled.add(url)
                    lock.release()

                try:
                    # Perform request. Check for errors.
                    # If it's okay dig inside for links.
                    r = s.get(url, timeout=REQUESTS_TIMEOUT)
                    r.raise_for_status()
                    find_links_in_html(r, base_url, all_links, logger)
                except Exception as e:
                    logger.warning(f'(crawl): {str(e)}')
            else:
                logger.debug('Could not acquire lock')
                pass

            # Prevent flooding target web server.
            sleep(1)
    logger.debug('Ending thread.')


@click.command()
@click.option('--nthreads', default=5, help='Number of threads',
              show_default=5)
@click.option('--output', default='endpoints_tree.txt',
              help='Output file location', show_default='endpoints_tree.txt')
@click.option('--all-links', is_flag=True)
@click.argument('url')
def crawler(nthreads=None, url=None, output=None, all_links=None):
    """
    Web crawler starts from URL to all found links under the same netloc.
    """
    # Create logger object
    logger = logging.getLogger('crawler')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('crawler.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s' +
                                  ' - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Check if URL is valid
    url = url
    if not checkers.is_url(url):
        logger.error(f'The url you have entered is not valid. URL: {str(url)}')
        exit(1)

    num_threads = nthreads
    output = output
    all_links = all_links

    logger.info('Starting crawler...')
    logger.info(f'URL: {str(url)}')
    logger.info(f'Number of threads: {str(num_threads)}')
    logger.info(f'Output: {str(output)}')

    # Requests follows redirections so we need to set initial base_url outside.
    parsed_url = urlsplit(url)
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}/'

    # Place URL into a queue.
    to_crawl.put(url)

    # Create threads.
    crawler_threads = list()
    for _ in range(int(num_threads)):
        crawler_threads.append(Thread(target=crawl, args=(base_url, all_links,
                                      logger,)))

    # Start first thread than wait some time for first crawl to complete.
    # Afterwards start remaining threads.
    first_thread = True
    for thread in crawler_threads:
        thread.start()
        if first_thread:
            sleep(REQUESTS_TIMEOUT)
            first_thread = False

    # Wait for all threads to finish.
    for thread in crawler_threads:
        thread.join()

    # Print the result to a file and also to standard output.
    print_results_to_file(endpoints, output, logger)
    print_results_to_stdout(endpoints, logger)

    return


def print_results_to_stdout(local_endpoints_dict, logger):
    if not isinstance(local_endpoints_dict, dict):
        logger.error('local_endpoints_dict is not a dictionary. Type: ' +
                     f'{type(local_endpoints_dict)}')
        return

    for key in local_endpoints_dict.keys():
        print(f'Links found on \'{str(key)}\':')
        for value in local_endpoints_dict[key]:
            print(f'\t- {value}')


def print_results_to_file(endpoints, output_file_name, logger):
    try:
        with open(output_file_name, 'w') as f:
            pp = pprint.PrettyPrinter(indent=4, stream=f)
            pp.pprint(endpoints)
        logger.info('Successfully wrote output file.')
    except Exception as e:
        logger.error(f'(print_results_to_file): {str(e)}')


if __name__ == '__main__':
    crawler()
    exit(0)
