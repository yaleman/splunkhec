#!/usr/bin/env python3

""" tests splunkhec.splunklogger """

import pytest
from loguru import logger
from splunkhec.splunklogger import SplunkLogger


try:
    import testconfig # type: ignore
except ImportError:
    pytest.skip(allow_module_level=True)


def test_splunklogger() -> None:
    """ does some really quick tests """
    splunklogger = SplunkLogger(endpoint=f"https://{testconfig.SERVER}/services/collector",
                                token=testconfig.TOKEN,
                                sourcetype="splunklogger_test",
                                index_name="test")
    logger.add(splunklogger.splunk_logger)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")

    # pylint: disable=line-too-long
    print(f"Logs are likely available at: https://{testconfig.SERVER}/app/search/search/?q=search%20index%3Dtest%20sourcetype%3Dsplunklogger_test&display.page.search.mode=fast&earliest=-15m%40m&latest=now")
