""" utility functions for splunkhec """
from uuid import UUID



def validate_token_format(token: str) -> bool:
    """ validates that it looks like a valid token """
    if not isinstance(token, str):
        raise TypeError(f"Token should be type 'str', got {type(token)}")
    try:
        UUID(token)
    except ValueError:
        raise ValueError("Token is not a valid UUID") # pylint: disable=raise-missing-from
    return True

DEFAULT_ENDPOINT = '/services/collector'
