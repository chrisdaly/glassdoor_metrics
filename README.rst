Glassdoor Metrics
--------
Pulls data from glassdoor's unofficial metrics API and also scrapes review counts and company metadata from the webpage.


Basic usage::
	
    >>> from glassdoor_metrics import Metrics
    >>>
    >>> company_id = '16'
    >>> file_path = "./{}.xlsx".format("test")
    >>> metrics = Metrics(company_id)
    >>> data = metrics.data
    >>> metrics.output_data(data, file_path)