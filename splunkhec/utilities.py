""" utility functions for splunkhec """
from uuid import UUID
from urllib.parse import urlparse
from loguru import logger
import requests



def validate_token_format(token: str):
    """ validates that it looks like a valid token """
    if not isinstance(token, str):
        raise TypeError(f"Token should be type 'str', got {type(token)}")
    try:
        UUID(token)
    except ValueError:
        raise ValueError("Token is not a valid UUID")
    return True





DEFAULT_ENDPOINT = '/services/collector'


def do_get_request(**kwargs):
    """ does a post request to an endpoint """
    endpoint = kwargs.get('endpoint', DEFAULT_ENDPOINT)
    if not kwargs:
        kwargs = {}
    if 'uri' in kwargs:
        uri = kwargs.get('uri')
    elif 'server' not in kwargs:
        raise ValueError("Need to specify one of uri or server+endpoint")
    else:
        uri = make_uri(kwargs.get('server'), endpoint, kwargs.get('secure', True))
    headers = make_headers(kwargs.get('token'), kwargs.get('headers'))
    response = requests.get(uri,
                             headers=kwargs.get('headers', {}),
                             params=kwargs.get('params'),
                             )
    return response