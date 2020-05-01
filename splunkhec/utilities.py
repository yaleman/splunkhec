""" utility functions for splunkhec """
from uuid import UUID
from urllib.parse import urlparse
from functools import lru_cache
import requests

URI_CACHE_MAXSIZE = 1024


def validate_token_format(token: str):
    """ validates that it looks like a valid token """
    if not isinstance(token, str):
        raise TypeError(f"Token should be type 'str', got {type(token)}")
    try:
        UUID(token)
    except ValueError:
        raise ValueError("Token is not a valid UUID")
    return True

@lru_cache(maxsize=URI_CACHE_MAXSIZE)
def make_uri(server: str, endpoint: str, secure: bool = True):
    """ turns things into a useful URI """
    # make sure endpoint has a leading slash
    if not endpoint.startswith("/"):
        endpoint = f'/{endpoint}'
    # strip trailing slash off server
    if server.endswith('/'):
        server = server[:-1]

    if not (server.startswith("http://") or server.startswith("https://")):
        if secure:
            server = f'https://{server}'
        else:
            server = f"http://{server}"
    elif server.startswith('http://') and secure:
        server = server.replace('http://', 'https://')
    
    if server.endswith(':443') and server.startswith('http://'):
        raise ValueError("Are you sure you want to run HTTP on port 443?")

    elif server.startswith('https://') and not secure:
        raise ValueError("HTTPS specified and secure == False")
    
    elif server.startswith("http://") and secure:
        raise ValueError("HTTPS specified and secure == True")
    uri = f'{server}{endpoint}'
    # check our own work
    urlparse(uri)
    return uri

def make_headers(token: str, headers: dict ):
    """ makes some basic headers """
    if not headers:
        headers = {}
    headers['Authorization'] = f"Splunk {token}"
    # TODO make testing for this
    return headers

def do_post_request(token: str, **kwargs):
    """ does a post request to and endpoint """
    if not kwargs:
        kwargs = {}
    if 'uri' in kwargs:
        uri = kwargs.get('uri')
    elif 'server' not in kwargs or 'endpoint' not in kwargs:
        raise ValueError("Need to specify one of uri or server+endpoint")
    else:
        uri = make_uri(kwargs.get('server'), kwargs.get('endpoint'), kwargs.get('secure', True))
    headers = make_headers(token, kwargs.get('headers'))
    response = requests.get(uri,
                             headers=headers,
                             data=kwargs.get('data'),
                             )
    return response

def do_get_request(token: str, **kwargs):
    """ does a post request to and endpoint """
    if not kwargs:
        kwargs = {}
    if 'uri' in kwargs:
        uri = kwargs.get('uri')
    elif 'server' not in kwargs or 'endpoint' not in kwargs:
        raise ValueError("Need to specify one of uri or server+endpoint")
    else:
        uri = make_uri(kwargs.get('server'), kwargs.get('endpoint'), kwargs.get('secure', True))
    headers = make_headers(token, kwargs.get('headers'))
    response = requests.get(uri,
                             headers=kwargs.get('headers', {}),
                             params=kwargs.get('params'),
                             )
    return response