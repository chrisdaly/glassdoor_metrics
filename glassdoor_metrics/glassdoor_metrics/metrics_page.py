import copy
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup as BS


class MetricsPage(object):
    def __init__(self, soup):
        self.soup = soup

    @property
    def review_containers(self):
        review_feed = self.soup.find("ol", class_="empReviews")
        review_containers = review_feed.findChildren("li", recursive=False)
        return review_containers

    @property
    def next_page_url(self):
        atag = self.soup.find("li", "next").find("a")
        if atag is not None:
            return "https://www.glassdoor.co.uk" + atag["href"]

    def reviews(self):
        for rc in self.review_containers:
            yield Review(rc).parse()

    @classmethod
    def from_response(cls, response):
        soup = BS(response.text, "html5lib")
        return cls(soup)

    @classmethod
    def from_html(cls, html):
        soup = BS(html, "html5lib")
        return cls(soup)
