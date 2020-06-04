#!/usr/bin/env python3
""" tests the health endpoint """

import re
#import pytest
from uuid import uuid4

from loguru import logger
import requests_mock
from splunkhec import splunkhec

import testconfig

URLMATCHER = re.compile('.*')

def test_is_healthy_200():
    """ tests a working one """
    expected_response = '{"text":"HEC is healthy","code":17}'
    with requests_mock.mock() as mock:
        hec = splunkhec(server='https://example.com:8088', token=str(uuid4()))
        mock.post(URLMATCHER, text=expected_response, status_code=200)
        assert hec.send_test_event()

def test_is_healthy_503():
    """ tests an endpoint returning 503 """
    expected_response = '{"text":"HEC is healthy","code":17}'
    with requests_mock.mock() as mock:
        hec = splunkhec(server='https://example.com:8088', token=str(uuid4()))
        mock.post(URLMATCHER, text=expected_response, status_code=503)
        assert not hec.send_test_event()


def test_is_healthy_400():
    """ tests an endpoint returning 400 """
    expected_response = '{"text":"HEC is healthy","code":17}'
    with requests_mock.mock() as mock:
        hec = splunkhec(server='https://example.com:8088', token=str(uuid4()))
        mock.post(URLMATCHER, text=expected_response, status_code=400)
        assert not hec.send_test_event()

if __name__ == '__main__':
    testhec = splunkhec(testconfig.SERVER)
    logger.debug(testhec.send_test_event(token=testconfig.TESTTOKEN))
