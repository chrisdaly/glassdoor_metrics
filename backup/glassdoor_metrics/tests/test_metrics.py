import unittest
from unittest.mock import patch
from glassdoor_metrics import get_all_company_data


class TestReviewPage(unittest.TestCase):
    def setUp(self):
        self.params = {
            "filter.defaultEmploymentStatuses": 'false',
            "filter.defaultLocation": 'false'
        }

          # file_path = "./tests/glassdoor_reviews_test.html"
          #  with open(file_path, "r", encoding='utf-8') as f:
          #       html = f.read()
          #   self.review_page = ReviewPage.from_html(html)

    def test_api_call(self):
        get_all_company_data(self.headers, params=self.params)

    def test_metrics(self):
        expected_data = {
            'id': '12449',
            'title': 'Good but needs improvement'
        }
        self.assertDictEqual(list(self.review_page.reviews())[0], expected_data)


if __name__ == '__main__':
    unittest.main()
