from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='glassdoor_metrics',
      version='0.3',
      description="Extracts all metrics on a given company's glassdoor page using the webpage itself and the unofficial API.",
      long_description=readme(),
      url='https://github.com/w2ogroup/Notebooks/tree/master/Glassdoor%20MReviews',
      author='Chris Daly',
      author_email='cdaly@w2ogroup.com',
      license='MIT',
      packages=['glassdoor_metrics'],
      install_requires=['bs4', 'lxml', 'requests', 'pandas', ],  # 'lxml'
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose']
      )
