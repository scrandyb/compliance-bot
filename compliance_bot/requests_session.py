"""Utils for creating a session object pre-configured with retries and auth headers"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def requests_retry_session(
    retries=5,
    backoff_factor=0.25,
    # retry on 429 (rate limit exceeded) plus common 5xx errors
    status_forcelist=(429, 500, 501, 502, 503, 504),
    bearer_token = ""
):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    if bearer_token:
        session.headers.update({"Authorization": "Bearer {}".format(bearer_token)})
    return session
