
import unittest
from rose import EventLoop

import imp
import os

test_events = imp.load_source('test_events', os.path.join(os.path.dirname(__file__), '../asyncio/tests/test_events.py'))


class RoseEventLoopTests(test_events.EventLoopTestsMixin, unittest.TestCase):
    def create_event_loop(self):
        return EventLoop()


if __name__ == '__main__':
    unittest.main()
