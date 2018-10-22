import os
import logging
import socket
from logging.handlers import SysLogHandler


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


def setup_papertrail(papertrail_hostport):
    if ':' not in papertrail_hostport:
        raise ValueError('papertrail_hostport required to be host:port')

    host, port = papertrail_hostport.split(':')
    syslog = SysLogHandler(address=(host, int(port)))
    syslog.addFilter(ContextFilter())

    _format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
    formatter = logging.Formatter(_format, datefmt='%b %d %H:%M:%S')
    syslog.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(syslog)
    logger.setLevel(logging.INFO)

    return logger
