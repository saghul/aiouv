"""Utilities shared by tests."""

import functools
import logging
import unittest

from . import events
from . import tasks

def sync(gen):
    @functools.wraps(gen)
    def wrapper(*args, **kw):
        return events.get_event_loop().run_until_complete(
            tasks.Task(gen(*args, **kw)))

    return wrapper


class LogTrackingTestCase(unittest.TestCase):

    def setUp(self):
        self._logger = logging.getLogger()
        self._log_level = self._logger.getEffectiveLevel()

    def tearDown(self):
        self._logger.setLevel(self._log_level)

    def suppress_log_errors(self):
        if self._log_level >= logging.WARNING:
            self._logger.setLevel(logging.CRITICAL)

    def suppress_log_warnings(self):
        if self._log_level >= logging.WARNING:
            self._logger.setLevel(logging.ERROR)


try:
        from socket import socketpair
except ImportError:
    assert sys.platform == 'win32'
    """A socket pair usable as a self-pipe, for Windows.

    Origin: https://gist.github.com/4325783, by Geert Jansen.  Public domain.
    """

    import errno
    import socket

    def socketpair(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
        """Emulate the Unix socketpair() function on Windows."""
        # We create a connected TCP socket. Note the trick with setblocking(0)
        # that prevents us from having to create a thread.
        lsock = socket.socket(family, type, proto)
        lsock.bind(('localhost', 0))
        lsock.listen(1)
        addr, port = lsock.getsockname()
        csock = socket.socket(family, type, proto)
        csock.setblocking(False)
        try:
            csock.connect((addr, port))
        except socket.error as e:
            if e.errno != errno.WSAEWOULDBLOCK:
                lsock.close()
                csock.close()
                raise
        ssock, _ = lsock.accept()
        csock.setblocking(True)
        lsock.close()
        return (ssock, csock)
