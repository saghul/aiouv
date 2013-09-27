
import threading
from tulip import events
from rose._events import EventLoop

__all__ = ['EventLoopPolicy', 'EventLoop']


class EventLoopPolicy(threading.local, events.AbstractEventLoopPolicy):
    """In this policy, each thread has its own event loop."""

    _event_loop = None

    def get_event_loop(self):
        if self._event_loop is None:
            self._event_loop = self.new_event_loop()
        return self._event_loop

    def set_event_loop(self, event_loop):
        assert event_loop is None or isinstance(event_loop, events.AbstractEventLoop)
        self._event_loop = event_loop

    def new_event_loop(self):
        return EventLoop()

