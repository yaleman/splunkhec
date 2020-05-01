#!/usr/bin/env python3
""" tests the health endpoint """

import re
#import pytest
from uuid import uuid4
import requests_mock
from splunkhec.health import is_healthy

URLMATCHER = re.compile('.*')

def test_is_healthy_200():
    """ tests a working one """

    expected_response = '{"text":"HEC is healthy","code":17}'
    with requests_mock.mock() as mock:
        mock.get(URLMATCHER, text=expected_response, status_code=200)
        assert is_healthy('https://example.com:8088', token=str(uuid4()))

def test_is_healthy_503():
    """ tests an endpoint returning 503 """

    expected_response = '{"text":"HEC is healthy","code":17}'
    with requests_mock.mock() as mock:
        mock.get(URLMATCHER, text=expected_response, status_code=503)
        assert not is_healthy('https://example.com:8088', token=str(uuid4()))


def test_is_healthy_400():
    """ tests an endpoint returning 400 """
    
    expected_response = '{"text":"HEC is healthy","code":17}'
    with requests_mock.mock() as mock:
        mock.get(URLMATCHER, text=expected_response, status_code=400)
        assert not is_healthy('https://example.com:8088', token=str(uuid4()))

