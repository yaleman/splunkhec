#pylint: disable=invalid-name
""" class for dealing with splunk HTTP event collectors """

from functools import lru_cache
from typing import Any, Dict, Optional
from urllib.parse import urlparse


from loguru import logger
import requests

from .utilities import validate_token_format

TEST_SOURCETYPE='test_hec_event'
URI_CACHE_MAXSIZE = 1024
DEFAULT_ENDPOINT = '/services/collector'

"""
services/collector/health
https://docs.splunk.com/Documentation/Splunk/8.0.2/RESTREF/RESTinput#services.2Fcollector.2Fhealth

<protocol>://<host>:8088/services/collector/health

This endpoint checks if HEC is healthy and able to accept new data from a load balancer. HEC health is determined if there is space available in the queue.

This endpoint works identically to services/health/1.0 but introduces a format version for future scalability. For more information, see services/collector/health/1.0.
Usage details

Port and protocol
By default, this endpoint works on port 8088 and uses HTTPs for transport. The port and HTTP protocol settings can be configured independently of settings for any other servers in your deployment.


Response codes
Status Code 	Description
200 	HEC is available and accepting input
400 	Invalid HEC token
503 	HEC is unhealthy, queues are full

"""
STATUS_CODE_MAP = {
    200 : {
        'result' : True,
        'description' : 'HEC is available and accepting input'
    },
    400 : {
        'result' : False,
        'description' : 'Invalid HEC token',
    },
    503 : {
        'result' : False,
        'description' : 'HEC is unhealthy, queues are full',
    },
}


def do_get_request(token: str, **kwargs: Any) -> requests.Response:
    """ does a post request to an endpoint """
    endpoint = kwargs.get('endpoint', DEFAULT_ENDPOINT)
    if not kwargs:
        kwargs = {}
    if 'uri' in kwargs:
        uri = kwargs['uri']
    elif 'server' not in kwargs:
        raise ValueError("Need to specify one of uri or server+endpoint")
    else:
        uri = make_uri(
            kwargs['server'],
            endpoint,
            kwargs.get('secure', True),
            )
    headers = make_headers(token, kwargs.get('headers', ""))
    response = requests.get(uri,
                             headers=headers,
                             params=kwargs.get('params'),
                             )
    return response

def make_headers(
    token: str,
    headers: Optional[Dict[str, Any]]=None,
    ) -> Dict[str, Any]:
    """ makes some basic headers """
    if headers is None:
        headers = {}
    headers['Authorization'] = f"Splunk {token}"
    # TODO make testing for this
    return headers

# @lru_cache(maxsize=URI_CACHE_MAXSIZE)
def make_uri(server: str, endpoint: str, secure: bool = True) -> str:
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

    if server.startswith('https://') and not secure:
        raise ValueError("HTTPS specified and secure == False")

    if server.startswith("http://") and secure:
        raise ValueError("HTTPS specified and secure == True")
    uri = f'{server}{endpoint}'
    # check our own work
    urlparse(uri)
    return uri

class splunkhec():
    """ HTTP event collector class for injecting events and testing things

        based on examples here:
        https://docs.splunk.com/Documentation/Splunk/latest/Data/HECExamples
        """
    def __init__(
        self,
        server: str,
        token: Optional[str] = None,
        **kwargs: Dict[str, Any],
        ) -> None:
        """ start up the jam
            expected variables
            - server (either the full hostname/port or just the hostname - eg https://example.com:8088 or example.com or example.com:8088)

            optional variables
            - token (a default token to use)
            - secure (bool: use https if true)
            - verbose (bool: how noisy to be)
        """
        if token is not None:
            if validate_token_format(token):
                self.token =token
        self.server = server
        self.secure = kwargs.get('secure', True)
        self.verbose = kwargs.get('verbose', False)

    def is_healthy(
        self,
        verbose: bool = False,
        ) -> Any:
        """
        if verbose: returns a dict {'result' : bool, 'description' : str}
        else: returns a bool
        """
        validate_token_format(self.token)

        uri = make_uri(
            self.server,
            "/services/collector/event",
            bool(self.secure),
        )
        headers = {
            'Authorisation' : f'Splunk {self.token}'
        }
        response = do_get_request(token=self.token, uri=uri, headers=headers)
        if response.status_code not in STATUS_CODE_MAP:
            raise ValueError(f"Unknown status code returned: {response.status_code} - {response.text}")
        if verbose:
            return [response.status_code]
        return STATUS_CODE_MAP[response.status_code].get('result')

    @classmethod
    def send_single_event(cls, event: Dict[str, Any]) -> None:
        """ send this a dict and it'll send the event to the server as JSON """
        if not isinstance(event, dict):
            raise TypeError(f"event should be a dict, got: {type(event)}")
        raise NotImplementedError("Haven't done this yet")

    def get_token(self, kwargs_object: Dict[str, Any]) -> str:
        """ figures out which token to use """
        if 'token' in kwargs_object:
            return str(kwargs_object['token'])
        if 'token' in dir(self):
            return str(getattr(self, 'token'))
        raise ValueError("Someone forgot to specify a token")

    def send_test_event(self, **kwargs: Dict[str, Any]) -> bool:
        """
        sends a test event to validate that the token works

        needs to be handed a sourcetype else it'll use TEST_SOURCETYPE

        returns True/False if it worked
        """
        logger.debug(f"sending test event: {kwargs}")

        data = {
            'event' : { 'token' : self.get_token(kwargs) },
            'sourcetype' : kwargs.get('sourcetype', TEST_SOURCETYPE),
        }
        response = self.do_post_request(
            data=data,
        )
        logger.debug(response)
        logger.debug(STATUS_CODE_MAP[response.status_code])
        if response.status_code in STATUS_CODE_MAP:
            return bool(STATUS_CODE_MAP[response.status_code]['result'])
        return False

    def do_post_request(
        self,
        **kwargs: Dict[str, Any],
        ) -> requests.Response:
        """ does a post request to an endpoint """
        endpoint = str(kwargs.get('endpoint', DEFAULT_ENDPOINT))
        response = requests.post(
            url=make_uri(
                self.server,
                endpoint=endpoint,
                secure=bool(self.secure),
                ),
            headers=make_headers(self.token),
            json=kwargs.get('data'),
            )
        return response
