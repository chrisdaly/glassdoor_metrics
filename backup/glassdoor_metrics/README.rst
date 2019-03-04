Glassdoor Reviews
--------

Basic usage::
	
    >>> from glassdoor_reviews import ReviewPage
    >>> import requests
    >>>
    >>> data = []
    >>> r = requests.get(url)
    >>> print(r.url)
    >>> rp = ReviewPage.from_response(r)
    >>>
	>>> for review in rp.reviews():
    >>> 	data.append(review)
    >>>
    >>> url = rp.next_page_url