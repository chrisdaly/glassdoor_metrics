from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='glassdoor_metrics',
      version='0.2',
      description="Extracts all rating data on a given company's glassdoor page.",
      url='https://github.com/w2ogroup/Notebooks/tree/master/Glassdoor%20Metrics',
      author='Chris Daly',
      author_email='cdaly@w2ogroup.com',
      license='MIT',
      packages=['glassdoor_metrics'],
      install_requires=['requests', 'pandas', 'bs4', 'lxml', 'xlsxwriter'],
      zip_safe=False)
