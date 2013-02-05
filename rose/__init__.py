
import threading
from tulip import events


class EventLoopPolicy(threading.local, events.EventLoopPolicy):
    """In this policy, each thread has its own event loop."""

    _event_loop = None

    def get_event_loop(self):
        """Get the event loop.

        This may be None or an instance of EventLoop.
        """
        if self._event_loop is None:
            self._event_loop = self.new_event_loop()
        return self._event_loop

    def set_event_loop(self, event_loop):
        """Set the event loop."""
        assert event_loop is None or isinstance(event_loop, events.EventLoop)
        self._event_loop = event_loop

    def new_event_loop(self):
        """Create a new event loop.

        You must call set_event_loop() to make this the current event
        loop.
        """
        from . import uv
        return uv.EventLoop()

