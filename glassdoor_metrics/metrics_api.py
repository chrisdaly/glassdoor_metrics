import copy
import requests
import re
import time
import pandas as pd
from bs4 import BeautifulSoup as BS
from functools import reduce


class MetricsAPI:
    def __init__(self, company_id):
        self.company_id = company_id
        self.url = "https://www.glassdoor.com/api/employer/{}-rating.htm?".format(company_id)
        self.headers = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Mobile Safari/537.36"}
        self.params_filter = {"filter.defaultEmploymentStatuses": "false", "filter.defaultLocation": "false"}
        self.employees_pasts = ["true", "false"]
        self.employee_types = ["REGULAR", "CONTRACT", "PART_TIME", "INTERN", "FREELANCE"]
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

    @property
    def data(self):
        data_raw = self.get_data_raw()
        data = {
            'Trend - Stars': self._parse_trend_data(data_raw, 'stars'),
            'Trend - Categories': self._parse_trend_data(data_raw, 'category'),
            'Distr - Stars': self._parse_stars_distribution(data_raw),
            'Distr - Category - Recommend': self._parse_distribution_data_for_category(data_raw, 'recommend'),
            'Distr - Category - CEO Approval': self._parse_distribution_data_for_category(data_raw, 'ceoRating'),
            'Distr - Category - Biz Outlook': self._parse_distribution_data_for_category(data_raw, 'bizOutlook')
        }
        return data

    def _api_get_data_from_endpoint(self, params=None):
        '''Makes a request to glassdoor's internal API and returns json.
        '''
        if params:
            self.params_filter.update(params)
        response = requests.get(self.url, headers=self.headers, params=self.params_filter)
        print("{} \t {}".format(response.status_code, response.url))

        try:
            assert response.status_code == 200
            return response.json()
        except AssertionError:
            print("-- Bad status code --")
            print(AssertionError)

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

    def _parse_distribution_data_for_category(self, data_raw, category):
        '''Parses raw data by keeping only keys of interest. Since each categorical
        distribution has a different label, they cannot be consolidated into one
        dictionary.
        '''
        d = data_raw['category']['distribution'][category]
        d = {'labels': d['labels'], 'values': d['values']}
        return d

    def _parse_trend_data(self, data_raw, category_type):
        '''Parses raw trend data into a a single dictionary suitable for a
        dataframe transformation.
        '''
        l = []
        for category, values in data_raw[category_type]['trend'].items():
            temp = {}
            temp[category] = values['employerRatings']
            temp['date'] = values['dates']
            df_temp = pd.DataFrame(temp)
            l.append(df_temp)

        df_temp = reduce(lambda x, y: pd.merge(x, y, "outer"), l)
        d = df_temp.to_dict(orient="records")
        return d

    def _parse_stars_distribution(self, data_raw):
        '''Parses raw distribution data into a a single dictionary suitable for a
        dataframe transformation.
        '''
        l = []
        for category in self.field_taxonomy['stars']:
            temp = {}
            temp[category] = data_raw['stars']['distribution'][category]['values']
            temp['stars'] = data_raw['stars']['distribution'][category]['labels']
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


if __name__ == '__main__':
    company_id = '437'
    metrics_api = MetricsAPI(company_id)
    data = metrics_api.data
