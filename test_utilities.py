#!/usr/bin/env python3

""" test harnesses for splunkhec.utilities """

import uuid
import pytest
import splunkhec.utilities

def test_validate_token_format_valid() -> None:
    """ use a valid token """
    guid = str(uuid.uuid4())
    assert splunkhec.utilities.validate_token_format(guid)

def test_validate_token_format_invalid1() -> None:
    """ use a clearly invalid token """
    guid = 12345
    with pytest.raises(TypeError):
        splunkhec.utilities.validate_token_format(guid) # type: ignore

def test_validate_token_format_invalid2() -> None:
    """ use a clearly invalid token """
    guid = '1123412341234'
    with pytest.raises(ValueError):
        splunkhec.utilities.validate_token_format(guid)

##############################################
# testing splunkhec.makeuri


def test_make_uri_valid_secure() -> None:
    """ tests a kinda valid result """
    server = 'example.com:8088'
    secure = True
    endpoint = '/event/collector/health'
    assert splunkhec.make_uri(server=server,
                              endpoint=endpoint,
                              secure=secure
                             ) == 'https://example.com:8088/event/collector/health'

def test_make_uri_valid_insecure() -> None:
    """ tests a valid result """
    server = 'example.com:8088'
    secure = False
    endpoint = '/event/collector/health'
    assert splunkhec.make_uri(server=server,
                              endpoint=endpoint,
                              secure=secure,
                              ) == 'http://example.com:8088/event/collector/health'

def test_make_uri_make_insecure() -> None:
    """ tests a kinda valid result """
    server = 'https://example.com:8088'
    secure = False
    endpoint = '/event/collector/health'
    with pytest.raises(ValueError):
        splunkhec.make_uri(server=server, endpoint=endpoint, secure=secure)


def test_make_uri_443_http() -> None:
    """ tests port 443 without secure """
    server = 'example.com:443'
    secure = False
    endpoint = '/event/collector/health'
    with pytest.raises(ValueError):
        splunkhec.make_uri(server=server, endpoint=endpoint, secure=secure)

def test_make_uri_http_443() -> None:
    """ tests a kinda valid result """
    server = 'https://example.com:443'
    secure = False
    endpoint = '/event/collector/health'
    with pytest.raises(ValueError):
        splunkhec.make_uri(server=server, endpoint=endpoint, secure=secure)

##############################################
# more tests?
