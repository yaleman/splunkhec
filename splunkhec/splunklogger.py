import requests
# dirty little logger for pushing from loguru to splunk HEC

class SplunkLogger(object):
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
        self.send_single_event(event=event_text.strip(),
                               index=self.index_name,
                               sourcetype=self.sourcetype,
                              )
        return True
