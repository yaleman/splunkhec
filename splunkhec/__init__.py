""" class for dealing with splunk HTTP event collectors """

from functools import lru_cache
from loguru import logger
from urllib.parse import urlparse
import requests

from .utilities import validate_token_format
from .health import is_healthy

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

def make_headers(token: str, headers: dict=None ):
    """ makes some basic headers """
    if not headers:
        headers = {}
    headers['Authorization'] = f"Splunk {token}"
    # TODO make testing for this
    return headers

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

class splunkhec():
    """ HTTP event collector class for injecting events and testing things

        based on examples here:
        https://docs.splunk.com/Documentation/Splunk/latest/Data/HECExamples
        """
    def __init__(self, server: str, **kwargs):
        """ start up the jam 
            expected variables
            - server (either the full hostname/port or just the hostname - eg https://example.com:8088 or example.com or example.com:8088)

            optional variables
            - token (a default token to use)
            - secure (bool: use https if true)
            - verbose (bool: how noisy to be)
        """
        if kwargs.get('token'):
            if validate_token_format(kwargs.get('token')):
                self.token = kwargs.get('token')
        self.server = server
        self.secure = kwargs.get('secure', True)
        self.verbose = kwargs.get('verbose', False)

    def is_healthy(self, verbose: bool = False):
        """ returns true/false if HEC is healthy """
        return is_healthy(
            server=self.server,
            token=self.token,
            secure=self.secure,
            verbose=verbose,
        )

    def send_single_event(self, event: dict):
        """ send this a dict and it'll send the event to the server as JSON """
        if not isinstance(event, dict):
            raise TypeError(f"event should be a dict, got: {type(event)}")
        raise NotImplementedError("Haven't done this yet")

    def get_token(self, kwargs_object):
        """ figures out which token to use """
        if 'token' in kwargs_object:
            return kwargs_object.get('token')
        elif 'token' in dir(self):
            return getattr(self, 'token')
        else:
            raise ValueError("Someone forgot to specify a token")

    def send_test_event(self, **kwargs):
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
        response = self.do_post_request(token=self.get_token(kwargs),
                                        data=data,
        )
        logger.debug(response)
        logger.debug(STATUS_CODE_MAP[response.status_code])
        return STATUS_CODE_MAP[response.status_code]['result']

    def do_post_request(self, **kwargs):
        """ does a post request to an endpoint """
        endpoint = kwargs.get('endpoint', DEFAULT_ENDPOINT)
        response = requests.post(url=make_uri(self.server, endpoint=endpoint, secure=self.secure),
                                 headers=make_headers(kwargs.get('token')),
                                 json=kwargs.get('data'),
                                 )
        return response