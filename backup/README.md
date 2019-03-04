# Glassdoor Metrics
Extracts all rating data on a given company's glassdoor page. 


## Installation
Clone this repository, cd into "glassdoor_metrics", and pip install -e .


## Example Usage
    import glassdoor_metrics

    company_id = 525
    file_path = './'
    data = glassdoor_metrics.get_all_company_data(company_id)
    glassdoor_metrics.output_data(data, file_path)

This repo contains additional files:

* Notebook: Glassdoor Metrics.ipynb 
* Sample input file: Companies.xlsx 
* Sample output file: Glassdoor Metrics - Novartis Pharmaceuticals.xlsx

These files align with W2O's folder structure (http://wiki.w2odst.com/wiki/Tutorial:Box_Folder_Structure) to help streamline workflow and organise data.

## Raw Data
There are 9 different fields that a glassdoor user rates their company on. These fields can be grouped into 2 separate data types based on how glassdoor asks users to rate them - by star rating and by categories. For example a user may give an overall rating of 3 stars to a company and choose the "Staying the same" category for the company's "Business Outlook".

### Stars

    * overall_rating
    * comp_and_benefits
    * culture_and_values
    * career_opportunities
    * work_life
    * senior_management

### Categorical

    * ceo_rating
    * biz_outlook
    * recommend

## Filters
Glassdoor automatically applies a default filter to your view of the website:
  
    filter.defaultLocation=false
    filter.employmentStatus=REGULAR
    filter.employmentStatus=PART_TIME

While ignoring location is useful, specifying job type is possibly not, as it cuts down on the number of ratings. Therefore the status filter is disabled when gathering the metrics, allowing us to consider every employee type.

    defaultEmploymentStatuses=false

## Data Retrieval - Webpage Scraping
There are two metrics that aren't possible to retrieve using the internal API described later:

    * company_reviews_count
    * ceo_reviews_count

These values are scraped using BeautifulSoup for each employee type combination:


    employees_pasts = ['true', 'false']
    employee_types = ['REGULAR', 'CONTRACT', 'PART_TIME',
                      'INTERN', 'FREELANCE']

This gives us a breakdown of how many reviews each employee segment is leaving. This information is in the output excel file's tab named:

* Reviews Breakdown


## Data Aggregation
The metrics pop-up window for a glassdoor page shows two different views for every field:

* Trend - the average value for that field for every month in the past 2 years.

* Distribution - the current amount of ratings per category in that field.

## Data Retrieval - Internal API
### Field-Type Combinations
The notebook utilises glassdoor's internal API to get the 18 combinations of field and type. These combinations are grouped by common index where appropriate (e.g. date, stars etc) but this isn't always possible (e.g. the distribution for ceo_rating contains the values "approve" and "disprove" which is different to the categories of every other field). This results in 6 tabs in the output excel file:

* Trend - Stars
* Trend - Categories
* Distr - Stars
* Distr - Category - Recommend
* Distr - Category - CEO Approval
* Distr - Category - Biz Outlook

Note: The above data has no filters applied. It's possible to pull the data for every filter combination (e.g. find how the ex-freelancers approval of the CEO has changed over time) but this seems too granular and not very useful.

### Company Name
The notebook makes one more additional call to the internal API to get the company name. This is a useful way to verify that the input id is the correct one for the intended company. This value, along with the company id and the date on which the scraping occurred is stored in the excel tab:

* Company Info  