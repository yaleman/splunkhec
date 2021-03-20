#!/usr/bin/env python3

""" tests splunkhec.splunklogger """

from loguru import logger
from splunkhec.splunklogger import SplunkLogger
from testconfig import TOKEN, SERVER

def test_splunklogger():
    """ does some really quick tests """
    splunklogger = SplunkLogger(endpoint=f"https://{SERVER}/services/collector",
                                token=TOKEN,
                                sourcetype="splunklogger_test",
                                index_name="test")
    logger.add(splunklogger.splunk_logger)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")

    print(f"Logs are likely available at: https://{SERVER}/app/search/search/?q=search%20index%3Dtest%20sourcetype%3Dsplunklogger_test&display.page.search.mode=fast&earliest=-15m%40m&latest=now")

