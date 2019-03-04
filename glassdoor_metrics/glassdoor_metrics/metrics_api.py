import copy
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup as BS
from functools import reduce
import re


class MetricsAPI:
    def __init__(self, company_id):
        self.company_id = company_id
        self.url = "https://www.glassdoor.com/api/employer/{}-rating.htm?".format(company_id)
        self.employees_pasts = ["true", "false"]
        self.employee_types = ["REGULAR", "CONTRACT", "PART_TIME", "INTERN", "FREELANCE"]
        self.headers = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Mobile Safari/537.36"}
        self.params_filter = {"filter.defaultEmploymentStatuses": "false", "filter.defaultLocation": "false"}
        self.field_taxonomy = {
            'stars': ['overallRating', 'cultureAndValues', 'workLife', 'seniorManagement', 'compAndBenefits', 'careerOpportunities'],
            'category': ['recommend', 'ceoRating', 'bizOutlook']
        }
        self.data_type_taxonomy = {
            "trend": {
                "columns": ["dates", "employerRatings"],
                "label": "employerRatings"
            },
            "distribution": {
                "columns": ["labels", 'values'],
                'label': "values"
            }
        }

    def __str__(self):
        return '{} {}'.format(self.company_name, self.company_id)

    def __repr__(self):
        return '{} {}'.format(self.company_name, self.company_id)

    def get_all_company_data(self):
        self.data_raw = self.get_data_raw()
        data = {
            'Company Info': self.company_info,
            'Reviews Breakdown': self.review_stats,
            'Trend - Stars': self._parse_trend_data('stars'),
            'Trend - Categories': self._parse_trend_data('category'),
            'Distr - Stars': self.stars_distribution,
            'Distr - Category - Recommend': self._parse_distribution_data_for_each_category('recommend'),
            'Distr - Category - CEO Approval': self._parse_distribution_data_for_each_category('ceoRating'),
            'Distr - Category - Biz Outlook': self._parse_distribution_data_for_each_category('bizOutlook')
        }
        return data

    def _api_get_data_from_endpoint(self, params=None):
        '''Makes a request to glassdoor's internal API and returns json.
        '''
        if params is not None:
            params_new = copy.deepcopy(self.params_filter)
            params_new.update(params)
        else:
            params_new = self.params_filter

        response = requests.get(self.url, headers=self.headers, params=params_new)
        print("{} \t {}".format(response.status_code, response.url))

        try:
            assert response.status_code == 200
        except AssertionError:
            print("-- Bad status code --")
            print(AssertionError)
            return None
        else:
            return response.json()

    def get_data_raw(self):
        '''Hits the API with every data type and category combination, stores the
        raw data to be processed later.
        '''
        data_raw = {}

        for category_type, categories in self.field_taxonomy.items():
            data_raw[category_type] = {}
            for data_type, data_info in self.data_type_taxonomy.items():
                data_raw[category_type][data_type] = {}
                for category in categories:
                    params = {'category': category, 'dataType': data_type}
                    params_new = copy.deepcopy(self.params_filter)
                    params_new.update(params)
                    data_category_type = self._api_get_data_from_endpoint(params=params)
                    data_raw[category_type][data_type][category] = data_category_type

        return data_raw

    def _parse_distribution_data_for_each_category(self, category):
        '''Parses raw data by keeping only keys of interest. Since each categorical
        distribution has a different label, they cannot be consolidated into one
        dictionary.
        '''
        d = self.data_raw['category']['distribution'][category]
        d = {'labels': d['labels'], 'values': d['values']}
        return d

    def _parse_trend_data(self, category_type):
        '''Parses raw trend data into a a single dictionary suitable for a
        dataframe transformation.
        '''
        l = []
        for category, values in self.data_raw[category_type]['trend'].items():
            temp = {}
            temp[category] = values['employerRatings']
            temp['date'] = values['dates']
            df_temp = pd.DataFrame(temp)
            l.append(df_temp)

        df_temp = reduce(lambda x, y: pd.merge(x, y, "outer"), l)
        d = df_temp.to_dict(orient="records")
        return d

    @property
    def stars_distribution(self):
        '''Parses raw distribution data into a a single dictionary suitable for a
        dataframe transformation.
        '''
        l = []
        for category in self.field_taxonomy['stars']:
            temp = {}
            temp[category] = self.data_raw['stars']['distribution'][category]['values']
            temp['stars'] = self.data_raw['stars']['distribution'][category]['labels']
            df_temp = pd.DataFrame(temp)
            l.append(df_temp)

        df_temp = reduce(lambda x, y: pd.merge(x, y, "outer"), l)
        d = df_temp.to_dict(orient="records")
        return d

    @property
    def company_name(self):
        params = {"category": "overallRating", "dataType": "trend"}
        data = self._api_get_data_from_endpoint(params=params)
        return data["employerName"]

    @property
    def company_info(self):
        '''Gets the company's name from the API. Serves as sanity check to ensure that
        the user input (company ID) refers to the correct company.
        '''
        company_info = [
            {'labels': 'company_name',
             'values': self.company_name},
            {'labels': 'company_id',
             'values': self.company_id},
            {'labels': 'date_scraped',
             'values': time.strftime(str(pd.to_datetime('today').date()))}
        ]
        return company_info

    @property
    def review_stats(self):
        '''Extracts the number of reviews on the webpage using every filter combo.
        These are the only values that aren't accessible via the API.
        '''
        l = []
        for past in self.employees_pasts:
            for type_ in self.employee_types:
                url = 'https://www.glassdoor.com/Reviews/-Reviews-E{}.htm'.format(company_id)
                params = {'filter.includePastEmployees': past, 'filter.EmploymentStatus': type_}
                params_new = copy.deepcopy(self.params_filter)
                params_new.update(params)

                response = requests.get(url, params=params_new, headers=self.headers)
                soup = BS(response.text, 'lxml')
                reviews = self._parse_soup_for_reviews(soup)
                reviews.update({'past_employees': past, 'employees_type': type_})
                l.append(reviews)
        return l

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

    @staticmethod
    def convert_camel_to_snake_case(name):
        snake_re = re.compile('([A-Z]+)')
        return snake_re.sub(r'_\1', name).lower()

    @staticmethod
    def find_and_set_index(df):
        columns_primary = ['date', 'stars', 'labels', 'type', 'employees_type']
        for each in columns_primary:
            if each in df.columns:
                df = df.set_index(each)
        return df

    @staticmethod
    def format_df(df):
        '''Cleans up the dataframe so that it's easier to process in python
        and easier to read in excel.
        '''
        df = df.round(2)
        df.columns = list(map(MetricsAPI.convert_camel_to_snake_case, df.columns))
        if 'stars' in df.columns:
            df['stars'] = df['stars'].apply(lambda x: x.split()[0])

        for each in ['type', 'labels', 'company_reviews_count', 'employees_type']:
            if each in df.columns:
                df[each] = df[each].apply(lambda x: x.lower().replace(' ', '_'))
                # df = df.set_index(each)

        df = MetricsAPI.find_and_set_index(df)
        return df

    @staticmethod
    def output_data(data, file_path):
        writer = pd.ExcelWriter(file_path, options={'strings_to_urls': False}, engine='xlsxwriter')
        for k, v in data.items():
            df = pd.DataFrame(v)
            df = df.fillna('0')
            df = MetricsAPI.format_df(df)
            df.to_excel(writer, k, index=True)
        writer.save()


if __name__ == '__main__':
    for company_id in ['437', '16', '925157', '12115', '119', '2212', '901352', '1267780']:
        metrics_api = MetricsAPI(company_id)
        file_path = "./{}.xlsx".format(metrics_api.company_name)
        data = metrics_api.get_all_company_data()
        metrics_api.output_data(data, file_path)

    # company_id = '437'
    # metrics_api = MetricsAPI(company_id)
    # print(metrics_api.review_stats)
