
import unittest

from tulip import test_utils
from tulip import events_test

from rose import uv_events


class RoseEventLoopTests(events_test.EventLoopTestsMixin, test_utils.LogTrackingTestCase):
    def create_event_loop(self):
        return uv_events.EventLoop()


if __name__ == '__main__':
    unittest.main()
