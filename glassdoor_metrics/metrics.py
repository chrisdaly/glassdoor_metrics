import re
import pandas as pd

from .metrics_webpage import MetricsWebPage
from .metrics_api import MetricsAPI


class Metrics:
    def __init__(self, company_id):
        self.company_id = company_id

    def __str__(self):
        return '{}'.format(self.company_id)

    def __repr__(self):
        return '{}'.format(self.company_name)

    @property
    def data(self):
        metrics_webpage = MetricsWebPage(self.company_id)
        metrics_api = MetricsAPI(self.company_id)
        data = {}
        data.update(metrics_webpage.data)
        data.update(metrics_api.data)
        return data

    def convert_camel_to_snake_case(name):
        snake_re = re.compile('([A-Z]+)')
        return snake_re.sub(r'_\1', name).lower()

    def find_and_set_index(df):
        columns_primary = ['date', 'stars', 'labels', 'type', 'employees_type']
        for each in columns_primary:
            if each in df.columns:
                df = df.set_index(each)
        return df

    def format_df(df):
        '''Cleans up the dataframe so that it's easier to process in python
        and easier to read in excel.
        '''
        df = df.round(2)
        df.columns = list(map(Metrics.convert_camel_to_snake_case, df.columns))
        if 'stars' in df.columns:
            df['stars'] = df['stars'].apply(lambda x: x.split()[0])

        for each in ['type', 'labels', 'company_reviews_count', 'employees_type']:
            if each in df.columns:
                df[each] = df[each].apply(lambda x: x.lower().replace(' ', '_'))

        df = Metrics.find_and_set_index(df)
        return df

    @staticmethod
    def output_data(data, file_path):
        writer = pd.ExcelWriter(file_path, options={'strings_to_urls': False}, engine='xlsxwriter')
        for k, v in data.items():
            df = pd.DataFrame(v)
            df = df.fillna('0')
            df = Metrics.format_df(df)
            df.to_excel(writer, k, index=True)
        writer.save()


if __name__ == '__main__':
    company_id = '16'
    metrics = Metrics(company_id)
    data = metrics.data
    file_path = "./{}.xlsx".format("test")
    metrics.output_data(data, file_path)
