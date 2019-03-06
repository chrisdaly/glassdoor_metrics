import unittest
import requests
import json
from bs4 import BeautifulSoup as BS
from glassdoor_metrics import Metrics, MetricsAPI, MetricsWebPage


class TestAPI(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.company_id = '16'
        self.metrics_api = MetricsAPI(self.company_id)
        file_path = "./tests/glassdoor_metrics_api_data_raw.txt"
        with open(file_path, "r", encoding='utf-8') as f:
            self.data_raw = json.loads(f.read())

    def test_api_call(self):
        data = self.metrics_api._api_get_data_from_endpoint()
        self.assertIsInstance(data, dict)

    def test_parsing_category(self):
        actual = self.metrics_api._parse_distribution_data_for_category(self.data_raw, 'recommend')
        expected = {'labels': ['Yes', 'No'], 'values': [410, 241]}
        self.assertEqual(actual, expected)

    def test_parsing_stars(self):
        actual = self.metrics_api._parse_stars_distribution(self.data_raw)[0]
        expected = {
            'overallRating': 87,
            'stars': '1 Star',
            'cultureAndValues': 107,
            'workLife': 90,
            'seniorManagement': 153,
            'compAndBenefits': 54,
            'careerOpportunities': 115
        }
        self.assertEqual(actual, expected)

    def test_parsing_trends(self):
        actual = self.metrics_api._parse_trend_data(self.data_raw, 'category')[0]
        expected = {'recommend': 0.628047, 'date': '2019/3/3', 'ceoRating': 0.763993, 'bizOutlook': 0.494446}
        self.assertEqual(actual, expected)


class TestWebPage(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.company_id = '16'
        self.metrics_webpage = MetricsWebPage(self.company_id)
        file_path = "./tests/glassdoor_metrics_webpage.html"
        with open(file_path, "r", encoding='utf-8') as f:
            self.html = f.read()
            self.soup = BS(self.html, 'lxml')

    def test_soup_parser(self):
        actual = self.metrics_webpage._parse_soup_for_reviews(self.soup)
        expected = {'ceo_reviews_count': None, 'company_reviews_count': '2228'}
        self.assertEqual(actual, expected)

    def test_json_parsing(self):
        actual = self.metrics_webpage.get_json_text(self.soup)[0].get('employer')
        expected = {
            'size': '10000--1',
            'sector': 'Insurance',
            'sectorId': '10014',
            'industry': 'Insurance Carriers',
            'industryId': '200066',
            'name': 'Aetna',
            'id': '16',
            'profileId': '16',
            'location': 'Hartford',
            'locationId': '1148399',
            'locationType': 'C'
        }
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    test_classes_to_run = [TestAPI, TestWebPage]

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)
