import unittest

import requests

from crawler import Crawler

url = 'https://duckduckgo.com/about'
base_url = 'https://duckduckgo.com/'
num_threads = 2
output = 'endpoints.txt'
all_links = False


class CrawlerTest(unittest.TestCase):

    def setUp(self):
        self.crawler = Crawler(url=url,
                               num_threads=num_threads,
                               output=output,
                               all_links=all_links)

    def test_insert_url_into_endpoints_dict(self):
        self.crawler.insert_url_into_endpoints_dict(base_url)

        self.assertIn(base_url, self.crawler.endpoints)

    def test_is_link_interesting(self):
        self.crawler.is_link_interesting(url, base_url, base_url)

        self.assertIn(base_url, self.crawler.endpoints)
        self.assertIn(url, self.crawler.crawl_set)
        self.assertIn(url, self.crawler.to_crawl.get())

    def test_duckduckgo(self):
        true_response = {
            'https://duckduckgo.com/': {
                'https://duckduckgo.com/about'
            }
        }  # Fetched 27 Jan 2021.

        r = requests.get(base_url)

        self.crawler.find_links_in_html(request=r,
                                        base_url=base_url,
                                        all_links=False)

        self.assertIn(r.url, self.crawler.endpoints)
        self.assertEqual(true_response, self.crawler.endpoints)

    def test_duckduckgo_about(self):
        true_response = {
            'https://duckduckgo.com/about': {
                'https://duckduckgo.com/',
                'https://duckduckgo.com/about',
                'https://duckduckgo.com/app',
                'https://duckduckgo.com/assets/email/DuckDuckGo-Privacy-Weekly_sample.png',
                'https://duckduckgo.com/donations',
                'https://duckduckgo.com/hiring',
                'https://duckduckgo.com/press',
                'https://duckduckgo.com/privacy',
                'https://duckduckgo.com/traffic'
            }
        }  # Fetched 27 Jan 2021.

        r = requests.get(url)

        self.crawler.find_links_in_html(request=r,
                                        base_url=base_url,
                                        all_links=False)

        self.assertIn(r.url, self.crawler.endpoints)
        self.assertIn(r.url, self.crawler.crawl_set)
        self.assertEqual(true_response, self.crawler.endpoints)


if __name__ == '__main__':
    unittest.main()
