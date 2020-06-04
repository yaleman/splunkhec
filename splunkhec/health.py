

from loguru import logger
from .utilities import validate_token_format, do_get_request


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
    #if verbose:
    #    return STATUS_CODE_MAP[response.status_code]
    #else:
    #    return STATUS_CODE_MAP[response.status_code].get('result')
