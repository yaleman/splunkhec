#! /usr/bin/env python3

"""
Output module for Splunk HTTP Event Collector

Re-written in python3 by James Hodgkinson 2020
"""

import argparse
import json
from json.decoder import JSONDecodeError
import os
import queue
import select
import socket
import sys
import threading

import requests
from loguru import logger

CONFIG_FILE = "/etc/omsplunkhec.json"

def setup_logging(logger_object=logger, debug=False):
    """ handles logging configuration """
    if debug:
        logger_object.remove()
        logger_object.add(sys.stdout, level="DEBUG")
    else:
        logger_object.remove()
        logger_object.add(sys.stdout, level="INFO")

def load_config():
    """ loads the config file """
    if not os.path.exists(CONFIG_FILE):
        logger.error("Couldn't find config file {}", CONFIG_FILE)
        sys.exit(1)
    try:
        with open(CONFIG_FILE, 'r') as file_handle:
            config = json.load(file_handle)
    except JSONDecodeError as error_message:
        logger.error("Failed to import {} : {}", CONFIG_FILE, error_message)
        sys.exit(1)
    return config

HOSTNAME = socket.gethostname()

default_config = load_config()

parser = argparse.ArgumentParser()
parser.add_argument("--token",
                    default=default_config.get("token", ""),
                    type=str,
                    help="http event collector token",
                    )
parser.add_argument("--server",
                    default=default_config.get("server", ""),
                    help="http event collector hostname",
                    )
parser.add_argument("--port",
                    help="port",
                    default=default_config.get("port", "8088"),
                    )
parser.add_argument("--ssl",
                    help="use ssl",
                    action="store_true",
                    default=default_config.get("ssl", True),
                    )
parser.add_argument('--ssl_noverify',
                    action="store_false",
                    help="disable ssl validation",
                    default=default_config.get("ssl_noverify", True),
                    )
parser.add_argument("--source",
                    default=default_config.get("source", f"hec:syslog:{HOSTNAME}"),
                    )
parser.add_argument("--sourcetype",
                    default=default_config.get("sourcetype", None),
                    )
parser.add_argument("--index",
                    default=default_config.get("sourcetype", 'main'),
                    )
parser.add_argument("--host",
                    default=default_config.get("host", HOSTNAME),
                    )
parser.add_argument("--maxbatch",
                    help="max number of records allowed in one batch of requests for hec",
                    default=int(default_config.get("max_batch", 100)),
                    type=int,
                    )
parser.add_argument("--maxqueue",
                    help="max number of records to be read from rsyslog queued for transfer",
                    default=int(default_config.get("maxqueue", 1000)),
                    type=int,
                    )
parser.add_argument("--maxthreads",
                    help="max number of threads for work",
                    default=int(default_config.get("maxthreads", 10)),
                    type=int,
                    )
parser.add_argument("--debug",
                    help="turn on debug mode",
                    action="store_true",
                    default=bool(default_config.get("debug", False)),
                    )

args = parser.parse_args()

if args.debug:
    os.environ["LOGURU_LEVEL"] = "DEBUG"
else:
    os.environ["LOGURU_LEVEL"] = "INFO"
# this has to be imported after the debug checks to set the level
#pylint: disable=wrong-import-position

HEC_HEADERS = {"Authorization": "Splunk " + args.token}
# server_uri = '%s://%s:%s/services/collector/raw' % (protocol, args.server, args.port) # old way
if args.ssl:
    URI_PROTOCOL = "https"
else:
    URI_PROTOCOL = "http"
SERVER_URI = "%s://%s:%s/services/collector" % (
    URI_PROTOCOL,
    args.server,
    args.port,
)


def send_splunk_events(
        hec_url=SERVER_URI,
        **kwargs,
    ):
    """ pass it the endpoint, token and a string, and it'll submit the event """
    if 'event' not in kwargs:
        raise ValueError("need to have at least an event value")

    # if you haven't set a field, or none'd it, then just remove it
    for key in list(kwargs):
        if kwargs.get(key) is None:
            del kwargs[key]

    # turn them into a big batch if they're a list of events
    if isinstance(kwargs.get('event'), list):
        payload = []
        settings = [key for key in kwargs if key != 'event']
        for event in kwargs.get('event'):
            event_data = {'event' : event}
            for setting in settings:
                event_data[setting] = kwargs.get(setting)
            payload.append(event_data)

    # if it's not just a string, string it
    elif not isinstance(kwargs.get("event", ""), str):
        payload = {}
        payload["event"] = str(payload.get("event"))

    logger.debug(payload)
    response = requests.post(url=hec_url, json=payload, headers=HEC_HEADERS)
    logger.debug("response: {}", response.text)
    response.raise_for_status()
    return response

#pylint: disable=unused-argument
def handle_queue(message_queue, thread_queue_object, stop_event_object, cmdline_args):
    """This is the entry point where actual work needs to be done. It receives
    a list with all messages pulled from rsyslog. The list is of variable
    length, but contains all messages that are currently available. It is
    suggest NOT to use any further buffering, as we do not know when the
    next message will arrive. It may be in a nanosecond from now, but it
    may also be in three hours...
    """
    while not stop_event_object.is_set() or not message_queue.empty():
        try:
            data = []
            try:
                while True and len(data) < args.maxBatch:
                    data.append(message_queue.get(True, 1))
                    message_queue.task_done()
            except queue.Empty:
                pass
            if data:
                send_splunk_events(hec_url=SERVER_URI,
                                   event=data,
                                   index=cmdline_args.index,
                                   sourcetype=cmdline_args.sourcetype,
                                   host=HOSTNAME,
                                   )
        except queue.Empty:
            pass  # finalize output
    thread_queue_object.get()
    thread_queue_object.task_done()

LOG_FILE = "/var/log/splunkconnector.log"
# this is the main logger
try:
    logger.add(
        LOG_FILE,
        rotation="500MB",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
except PermissionError:
    logger.error("Can't write to {}", LOG_FILE)
logger.debug("starting up")

# skeleton config parameters
POLL_PERIOD = 0.2  # the number of seconds between polling for new messages
# set up the logger so we can send events through
# loguru to splunk, don't need to timestamp as rsyslog will add that

# -------------------------------------------------------
# This is plumbing that DOES NOT need to be CHANGED
# -------------------------------------------------------
# Implementor's note: Python seems to very agressively
# buffer stdouot. The end result was that rsyslog does not
# receive the script's messages in a timely manner (sometimes
# even never, probably due to races). To prevent this, we
# flush stdout after we have done processing. This is especially
# important once we get to the point where the plugin does
# two-way conversations with rsyslog. Do NOT change this!
# See also: https://github.com/rsyslog/rsyslog/issues/22


stop_event = threading.Event()
# stop_event.set()
maxAtOnce = args.maxBatch
msgQueue = queue.Queue(maxsize=args.maxQueue)
thread_queue = queue.Queue(maxsize=args.maxThreads)


for i in range(args.maxThreads):
    thread_queue.put(i)
    worker = threading.Thread(target=handle_queue,
                              args=(msgQueue, thread_queue, stop_event, args),
                              )
    worker.setDaemon(True)
    worker.start()

while not stop_event.is_set():
    while (not stop_event.is_set()
           and sys.stdin in select.select([sys.stdin], [], [], POLL_PERIOD)[0]
           ):
        while (not stop_event.is_set()
               and sys.stdin in select.select([sys.stdin], [], [], 0)[0]
               ):
            line = sys.stdin.readline()
            if line.strip():
                msgQueue.put(line.strip())
            else:  # an empty line means stdin has been closed
                stop_event.set()
                msgQueue.join()

logger.info("waiting for thread shutdown")
thread_queue.join()

sys.stdout.flush()  # very important, Python buffers far too much!
