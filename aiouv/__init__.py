
import asyncio
import threading

from ._events import EventLoop
from ._transports import connect_tcp, listen_tcp, connect_pipe, listen_pipe, create_udp_endpoint

__all__ = ['EventLoopPolicy', 'EventLoop',
           'connect_tcp', 'listen_tcp',
           'connect_pipe', 'listen_pipe',
           'create_udp_endpoint']


class EventLoopPolicy(threading.local, asyncio.events.AbstractEventLoopPolicy):
    """In this policy, each thread has its own event loop."""

    _event_loop = None

    def get_event_loop(self):
        if self._event_loop is None:
            self._event_loop = self.new_event_loop()
        return self._event_loop

    def set_event_loop(self, event_loop):
        assert event_loop is None or isinstance(event_loop, asyncio.events.AbstractEventLoop)
        self._event_loop = event_loop

    def new_event_loop(self):
        return EventLoop()

