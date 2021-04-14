#!python3
""" dirty little logger for pushing from loguru to splunk HEC """

from os import getenv
import time
import sys

try:
    import requests
except ImportError as error_message:
    sys.exit(f"Couldn't import requests, `python3 -m pip install requests` would be handy. Error: {error_message}") #pylint: disable=line-too-long

try:
    from loguru._defaults import LOGURU_FORMAT
except ImportError as error_message:
    sys.exit(f"Couldn't import loguru, `python3 -m pip install loguru` would be handy. Error: {error_message}") #pylint: disable=line-too-long


class SplunkLogger():
    """ this can help you to log directly to splunk HEC """
    def __init__(self,
                 endpoint: str,
                 token: str,
                 sourcetype: str="unknown",
                 index_name: str="main",
                 ):
        """using this
from splunklogger import SplunkLogger
from loguru import logger
splunklogger = SplunkLogger(endpoint="https://localhost:8088/services/collector",
                            token="mysupersecuretoken",
                            sourcetype="my_logging_sourcetype",
                            index_name="my_logging_index",
                            )
logger.add(splunklogger.splunk_logger)
"""
        self.endpoint = endpoint
        self.token = token
        self.sourcetype = sourcetype
        self.index_name = index_name

    def send_single_event(self,
                          **kwargs,
                          ):
        """ pass it the endpoint, token and a string, and it'll submit the event """
        if 'event' not in kwargs:
            raise ValueError("need to have at least an event value")
        headers = {
            'Authorization' : 'Splunk {}'.format(self.token)
        }
        payload = kwargs
        if not isinstance(payload['event'], str):
            payload['event'] = str(payload['event'])
        req = requests.post(url=self.endpoint, json=payload, headers=headers)
        req.raise_for_status()
        return req

    def splunk_logger(self, event_text):
        """ makes a callable for loguru to send to splunk """
        try:
            self.send_single_event(event=event_text.strip(),
                                   index=self.index_name,
                                   sourcetype=self.sourcetype,
                                  )
        # TODO: work out what exceptions to catch.. there's probably a lot.
        except Exception as error_message: # pylint: disable=broad-except
            print(f"Failed to send, error: {error_message}")
            time.sleep(5)
            self.splunk_logger(event_text)
        return True

def setup_logging(logger_object, debug: bool=True,
                    level_ljust=None,
                    use_default_loguru: bool=True,
                    log_sink=sys.stderr,
                    ) -> None:
    """ does logging configuration
        set use_default_loguru to false to make the format a bit quieter
            - handy for shell scripts where you're using loguru to be pretty, but maybe not with all the debugging stuff
        default logs to stderr, just like loguru https://github.com/Delgan/loguru/blob/master/loguru/_logger.py#L197

        example usage:
        splunklogger = SplunkLogger(endpoint=f"https://{SPLUNK_HEC_HOST}/services/collector",
                                    token=SPLUNK_HEC_TOKEN,
                                    sourcetype=SPLUNK_SOURCETYPE,
                                    index_name=SPLUNK_INDEX,
                                    )
        setup_logging(logger_object=logger,
                      log_sink=splunklogger.splunk_logger,
                      )
    """
    # use the one from the environment, where possible
    loguru_level=getenv('LOGURU_LEVEL', 'INFO')
    loguru_format = LOGURU_FORMAT

    if debug:
        loguru_level='DEBUG'
    elif not use_default_loguru:
        loguru_format = '<level>{message}</level>'

    if level_ljust:
        # TODO: I hate this string concatenation, but fstrings...
        loguru_format = loguru_format.replace('{level}', '{level: <'+level_ljust+'}')

    logger_object.remove()
    logger_object.add(sink=log_sink,
                      format=loguru_format,
                      level=loguru_level,
                      )

if __name__ == '__main__':
    print("This should not be used as a script", file=sys.stderr)
    sys.exit(1)
