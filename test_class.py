""" tests the class and usage of it """
from uuid import uuid4

# import requests_mock
from splunkhec import splunkhec

def test_init() -> None:
    """ basic init test """
    server = "https://example.com"
    token = str(uuid4())
    assert splunkhec(server=server, token=token)
