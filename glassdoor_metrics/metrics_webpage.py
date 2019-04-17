import copy
import time
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup as BS


class MetricsWebPage:
    def __init__(self, company_id):
        self.company_id = company_id
        self.url = 'https://www.glassdoor.com/Reviews/-Reviews-E{}.htm'.format(company_id)
        self.headers = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Mobile Safari/537.36"}
        self.params_filter = {"filter.defaultEmploymentStatuses": "false", "filter.defaultLocation": "false"}
        self.employees_pasts = ["true", "false"]
        self.employee_types = ["REGULAR", "CONTRACT", "PART_TIME", "INTERN", "FREELANCE"]
        self.rate_limit = 1

    def get_soup(self):
        time.sleep(self.rate_limit)
        response = requests.get(self.url, params=self.params_filter, headers=self.headers)
        print("{} \t {}".format(response.status_code, response.url))

        try:
            assert response.status_code == 200
        except AssertionError:
            print("-- Bad status code --")
            print(AssertionError)
            return None
        else:
            soup = BS(response.text, 'lxml')
            return soup

    def get_json_text(self, soup):
        script = soup.find('script', text=re.compile(r'window\.gdGlobals'))
        script = script.get_text().replace('\t', '').replace('\n', '').replace('\\', '')
        regex = r'window.gdGlobals \|\|(\[{.*?}\])'
        match = re.search(regex, script, re.MULTILINE)
        if match:
            json_text = match.group(1)
            json_text = json_text.replace("'", '"').replace('  ', '').replace('[,', '[')
            print(json_text)
            json_text = json.loads(json_text)
            return json_text
        else:
            return None

    @property
    def company_info(self):
        soup = self.get_soup()
        json_text = self.get_json_text(soup)
        data_employer = json_text[0]['employer']

        company_info = []
        for each in data_employer.keys():
            d = {'labels': each, 'values': data_employer.get(each)}
            company_info.append(d)
        return company_info

    @property
    def review_stats(self):
        '''Extracts the number of reviews on the webpage using every filter combo.
        These are the only values that aren't accessible via the API.
        '''
        l = []
        for past in self.employees_pasts:
            for type_ in self.employee_types:
                params = {'filter.includePastEmployees': past, 'filter.EmploymentStatus': type_}
                self.params_filter.update(params)
                soup = self.get_soup()
                reviews = self._parse_soup_for_reviews(soup)
                reviews.update({'past_employees': past, 'employees_type': type_})
                l.append(reviews)
        return l

    @property
    def data(self):
        data = {
            'Reviews Breakdown': self.review_stats,
            'Company Info': self.company_info
        }
        return data

    @staticmethod
    def _parse_soup_for_reviews(soup):
        '''Locates and parses the divs containing the ceo and company ratings.
        '''
        company_reviews_count = soup.find('div', class_='padTopSm margRtSm margBot minor')
        if company_reviews_count is not None:
            company_reviews_count = company_reviews_count.get_text().split()[0].replace(',', '')

        ceo_reviews_count = soup.find('div', class_='numCEORatings')
        if ceo_reviews_count is not None:
            ceo_reviews_count = ceo_reviews_count.get_text().split()[0].replace(',', '')

        d = {'ceo_reviews_count': ceo_reviews_count, 'company_reviews_count': company_reviews_count}
        return d


if __name__ == '__main__':
    company_id = '437'
    metrics_webpage = MetricsWebPage(company_id)
    # print(metrics_webpage.data)
    print(metrics_webpage.company_info)
