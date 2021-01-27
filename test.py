import unittest
from threading import Thread, Lock
from queue import Queue

from crawler import (crawl,
                     is_link_interesting,
                     find_links_in_html,
                     insert_url_into_endpoints_dict)

url = 'https://monzo.com/'


class Requireds:
    def __init__(self):
        self.endpoints = dict()
        self.to_crawl = Queue()
        self.already_crawled = set()
        self.crawl_set = set()
        self.lock = Lock()


class CrawlerTest(unittest.TestCase):

    def setUp(self):
        self.requireds = Requireds()

    def test_insert_url_into_endpoints_dict(self):
        insert_url_into_endpoints_dict(url)

        self.assertIn(url, self.endpoints)

    def test_is_link_interesting(self):
        this_link = '/asd'
        is_link_interesting(this_link, url, url, None)

        self.assertIn(url+this_link, self.endpoints[url])


if __name__ == '__main__':
    unittest.main()
