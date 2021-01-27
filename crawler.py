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
from bs4 import BeautifulSoup
from validator_collection import checkers

REQUESTS_TIMEOUT = 3
REQUESTS_RETRY_COUNT = 3
REQUESTS_BACKOFF_FACTOR = 1


class Crawler(object):
    def __init__(self, url, num_threads, output, all_links):
        self.endpoints = dict()
        self.to_crawl = Queue()
        self.already_crawled = set()
        self.crawl_set = set()
        self.lock = Lock()

        # Create logger object
        self.logger = logging.getLogger('crawler')
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler('crawler.log')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - ' +
                                      '%(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.url = url
        self.num_threads = num_threads
        self.output = output
        self.all_links = all_links

        # Requests follows redirections so we need to set initial
        # base_url outside.
        parsed_url = urlsplit(self.url)
        self.base_url = f'{parsed_url.scheme}://{parsed_url.netloc}/'

    def start(self):
        self.logger.info('Starting crawler...')
        self.logger.info(f'URL: {str(self.url)}')
        self.logger.info(f'Number of threads: {str(self.num_threads)}')
        self.logger.info(f'Output: {str(self.output)}')

        # Place URL into a queue.
        self.insert_url_into_crawl_target_set(self.url)

        # Create threads.
        crawler_threads = list()
        for _ in range(int(self.num_threads)):
            crawler_threads.append(Thread(target=self.thread_crawl,
                                          args=(self.base_url,
                                                self.all_links,)))

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

    def print_results(self):
        # Print the result to a file and also to standard output.
        self.print_results_to_file(self.endpoints, self.output)
        self.print_results_to_stdout(self.endpoints)

    def insert_url_into_endpoints_dict(self, url, url2=None):
        if url not in self.endpoints:
            self.endpoints[url] = set()
        if url2 is not None:
            self.endpoints[url].add(url2)

    def insert_url_into_crawl_target_set(self, url):
        if url not in self.crawl_set:
            self.crawl_set.add(url)
            self.to_crawl.put(url)

    def is_link_interesting(self, this_link, base_url, url):
        if this_link is None:
            return
        try:
            if this_link.startswith('/'):
                self.insert_url_into_endpoints_dict(url,
                                                    base_url+this_link[1:])
                self.insert_url_into_crawl_target_set(base_url+this_link[1:])
            elif this_link.startswith(base_url):
                self.insert_url_into_endpoints_dict(url, this_link)
                self.insert_url_into_crawl_target_set(this_link)
            else:
                pass
        except Exception as e:
            self.logger.error(f'(is_link_interesting): {str(e)}. Link: \
                        {str(this_link)}')

    def find_links_in_html(self, request, base_url, all_links):
        url = request.url
        html_text = request.text
        parsed_url = urlsplit(url)

        if not parsed_url.geturl().startswith(base_url):
            return

        self.insert_url_into_endpoints_dict(parsed_url.geturl())

        soup = BeautifulSoup(html_text, 'html.parser')
        if all_links:
            for link in soup.find_all(href=True):
                this_link = link.get('href')
                self.is_link_interesting(this_link, base_url, url)
        else:
            for link in soup.find_all('a'):
                this_link = link.get('href')
                self.is_link_interesting(this_link, base_url, url)

    def thread_crawl(self, base_url, all_links):
        self.logger.debug(f'Starting thread with base url: {base_url}')
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
                if not self.to_crawl.qsize() > 0:
                    break

                # Acquire a lock to prevent multiple threads doing
                # the same job.
                if self.lock.acquire(timeout=5):
                    url = self.to_crawl.get()
                    # Check whether the url was crawled before.
                    if url in self.already_crawled:
                        self.lock.release()
                        continue
                    else:
                        self.already_crawled.add(url)
                        self.lock.release()

                    try:
                        # Perform request. Check for errors.
                        # If it's okay dig inside for links.
                        r = s.get(url, timeout=REQUESTS_TIMEOUT)
                        r.raise_for_status()
                        self.find_links_in_html(r, base_url, all_links)
                    except Exception as e:
                        self.logger.warning(f'(crawl): {str(e)}')
                else:
                    self.logger.debug('Could not acquire lock')
                    pass

                # Prevent flooding target web server.
                sleep(1)
        self.logger.debug('Ending thread.')

    def print_results_to_stdout(self, local_endpoints_dict):
        if not isinstance(local_endpoints_dict, dict):
            self.logger.error('local_endpoints_dict is not a dictionary. ' +
                              f'Type: {type(local_endpoints_dict)}')
            return

        for key in local_endpoints_dict.keys():
            print(f'Links found on \'{str(key)}\':')
            for value in local_endpoints_dict[key]:
                print(f'\t- {value}')

    def print_results_to_file(self, endpoints, output_file_name):
        try:
            with open(output_file_name, 'w') as f:
                pp = pprint.PrettyPrinter(indent=4, stream=f)
                pp.pprint(endpoints)
            self.logger.info('Successfully wrote output file.')
        except Exception as e:
            self.logger.error(f'(print_results_to_file): {str(e)}')


@click.command()
@click.option('--nthreads', default=5, help='Number of threads.',
              show_default=5)
@click.option('--output', default='endpoints.txt',
              help='Output path.', show_default='endpoints.txt')
@click.option('--all-links', help='Include all resources.', is_flag=True)
@click.argument('url')
def crawler(nthreads=None, url=None, output=None, all_links=None):
    """
    Web crawler starts from URL to all found links under the same netloc.
    """
    # Check if URL is valid
    url = url
    if not checkers.is_url(url):
        print(f'The url you have entered is not valid. URL: {str(url)}')
        exit(1)

    num_threads = nthreads
    output = output
    all_links = all_links

    crawler = Crawler(url=url,
                      num_threads=num_threads,
                      output=output,
                      all_links=all_links)

    crawler.start()
    crawler.print_results()

    return


if __name__ == '__main__':
    crawler()
    exit(0)
