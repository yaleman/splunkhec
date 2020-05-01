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

from .utilities import validate_token_format, do_get_request, make_uri

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
def is_healthy(server: str, token: str, secure: bool = True, verbose: bool = False):
    """ 
    
    if verbose: returns a dict {'result' : bool, 'description' : str}
    else: returns a bool
    """
    validate_token_format(token)
    
    uri = make_uri(server, "/services/collector/event", secure)
    headers = {
        'Authorisation' : f'Splunk {token}'
    }
    response = do_get_request(token=token, uri=uri)
    if response.status_code not in STATUS_CODE_MAP:
        raise ValueError(f"Unknown status code returned: {response.status_code} - {response.text}")
    if verbose:
        return STATUS_CODE_MAP[response.status_code]
    else:
        return STATUS_CODE_MAP[response.status_code].get('result')

