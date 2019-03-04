import copy
import re
import requests
import pandas as pd
from time import strftime
from bs4 import BeautifulSoup as BS


def api_get_data_from_endpoint(company_id, params=None):
    '''Makes a request to glassdoor's internal API and returns json.
    '''
    url_base = 'https://www.glassdoor.com/api/employer/{}-rating.htm?'
    url = url_base.format(company_id)

    if params is not None:
        params_new = copy.deepcopy(params_filter)
        params_new.update(params)
    else:
        params_new = params_filter

    response = requests.get(url, headers=headers, params=params_new)

    try:
        assert response.status_code == 200
    except AssertionError:
        print('-- Bad status code --')
        print(AssertionError)
        return None
    else:
        return response.json()


def get_company_data(company_id=None):
    '''Gets the company's name from the API. Serves as sanity check to ensure that
    the user input (company ID) refers to the correct company.
    '''
    params = {'category': 'overallRating', 'dataType': 'trend'}
    data = api_get_data_from_endpoint(company_id, params=params)
    company_data = [{'labels': 'company_name',
                     'values': data['employerName']},
                    {'labels': 'company_id',
                     'values': data['employerId']},
                    {'labels': 'date_scraped',
                     'values': strftime(str(pd.to_datetime('today').date()))}]
    return company_data


def get_trends_and_distributions(company_id):
    '''Hits the API with every data type and category combination, stores the
    raw data to be processed later.
    '''
    data_raw = {}

    for category_type, categories in field_taxonomy.items():
        data_raw[category_type] = {}
        for data_type, data_info in data_type_taxonomy.items():
            data_raw[category_type][data_type] = {}
            for category in categories:
                params = {'category': category, 'dataType': data_type}
                params_new = copy.deepcopy(params_filter)
                params_new.update(params)
                data_category_type = api_get_data_from_endpoint(
                    company_id, params=params)
                data_raw[category_type][data_type][category] = data_category_type

    return data_raw


def parse_trend_data(data_raw, category_type):
    '''Parses raw trend data into a a single dictionary suitable for a
    dataframe transformation.
    '''
    d = {}
    for category, values in data_raw[category_type]['trend'].items():
        d[category] = values['employerRatings']
    d['date'] = values['dates']
    return d


def parse_distribution_data_for_all_stars(data_raw):
    '''Parses raw distribution data into a a single dictionary suitable for a
    dataframe transformation.
    '''
    d = {}
    for category in field_taxonomy['stars']:
        d[category] = data_raw['stars']['distribution'][category]['values']
    d['stars'] = data_raw['stars']['distribution'][category]['labels']
    return d


def parse_distribution_data_for_each_category(data_raw, category):
    '''Parses raw data by keeping only keys of interest. Since each categorical
    distribution has a different label, they cannot be consolidated into one
    dictionary.
    '''
    d = data_raw['category']['distribution'][category]
    d = {'labels': d['labels'], 'values': d['values']}
    return d


def format_df(df):
    '''Cleans up the dataframe so that it's easier to process in python
    and easier to read in excel.
    '''
    df = df.round(2)
    df.columns = list(map(convert_camel_to_snake_case, df.columns))
    if 'stars' in df.columns:
        df['stars'] = df['stars'].apply(lambda x: x.split()[0])

    for each in ['type', 'labels', 'company_reviews_count', 'employees_type']:
        if each in df.columns:
            df[each] = df[each].apply(lambda x: x.lower().replace(' ', '_'))
            # df = df.set_index(each)

    df = find_and_set_index(df)
    return df


def find_and_set_index(df):
    columns_primary = ['date', 'stars', 'labels', 'type', 'employees_type']
    for each in columns_primary:
        if each in df.columns:
            df = df.set_index(each)
    return df


def get_review_count_from_html(company_id):
    '''Extracts the number of reviews on the webpage using every filter combo.
    These are the only values that aren't accessible via the API.
    '''
    url_base = 'https://www.glassdoor.com/Reviews/-Reviews-E{}.htm'
    url = url_base.format(company_id)
    l = []

    for past in employees_pasts:
        for type_ in employee_types:
            params = {
                'filter.includePastEmployees': past,
                'filter.EmploymentStatus': type_}
            params_new = copy.deepcopy(params_filter)
            params_new.update(params)
            r = requests.get(url, params=params_new, headers=headers)
            soup = BS(r.text, 'lxml')
            reviews = parse_soup_for_reviews(soup)
            reviews.update({'past_employees': past, 'employees_type': type_})
            l.append(reviews)

    return l


def parse_soup_for_reviews(soup):
    '''Locates and parses the divs containing the ceo and company ratings.
    '''
    company_reviews_count = soup.find('div', {'class': 'padTopSm margRtSm margBot minor'})
    if company_reviews_count is not None:
        company_reviews_count = company_reviews_count.get_text().split()[
            0].replace(',', '')

    ceo_reviews_count = soup.find('div', {'class': 'numCEORatings'})
    if ceo_reviews_count is not None:
        ceo_reviews_count = ceo_reviews_count.get_text().split()[
            0].replace(',', '')

    d = {'ceo_reviews_count': ceo_reviews_count,
         'company_reviews_count': company_reviews_count}

    return d


def convert_camel_to_snake_case(name):
    return snake_re.sub(r'_\1', name).lower()


def get_all_company_data(company_id):
    data_raw = get_trends_and_distributions(company_id)
    data = {
        'Company Info': get_company_data(company_id),
        'Reviews Breakdown': get_review_count_from_html(company_id),
        'Trend - Stars': parse_trend_data(data_raw, 'stars'),
        'Trend - Categories': parse_trend_data(data_raw, 'category'),
        'Distr - Stars': parse_distribution_data_for_all_stars(data_raw),
        'Distr - Category - Recommend': parse_distribution_data_for_each_category(data_raw, 'recommend'),
        'Distr - Category - CEO Approval': parse_distribution_data_for_each_category(data_raw, 'ceoRating'),
        'Distr - Category - Biz Outlook': parse_distribution_data_for_each_category(data_raw, 'bizOutlook'),
    }
    return data


def output_data(data, file_path):
    writer = pd.ExcelWriter(file_path, options={'strings_to_urls': False}, engine='xlsxwriter')
    for k, v in data.items():
        df = pd.DataFrame(v)
        df = df.fillna('0')
        df = format_df(df)
        df.to_excel(writer, k, index=True)

    writer.save()


snake_re = re.compile('([A-Z]+)')

headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) \
     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Mobile \
     Safari/537.36'
}

params_filter = {
    "filter.defaultEmploymentStatuses": 'false',
    "filter.defaultLocation": 'false'
}

field_taxonomy = {
    'stars': ['overallRating', 'cultureAndValues', 'workLife', 'seniorManagement', 'compAndBenefits', 'careerOpportunities'],
    'category': ['recommend', 'ceoRating', 'bizOutlook']
}

data_type_taxonomy = {
    'trend': {
        'columns': ['dates', 'employerRatings'],
        'label': 'employerRatings'
    },
    'distribution': {
        'columns': ['labels', 'values'],
        'label': 'values'
    }
}

employees_pasts = ['true', 'false']
employee_types = ['REGULAR', 'CONTRACT', 'PART_TIME', 'INTERN', 'FREELANCE']

if __name__ == '__main__':
    data = get_all_company_data(6667)
    print(data)
