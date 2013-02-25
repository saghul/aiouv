
import unittest
from tulip import test_utils
from rose import uv_events

import sys
sys.path.append('../tulip/tests')
import events_test

class RoseEventLoopTests(events_test.EventLoopTestsMixin, test_utils.LogTrackingTestCase):
    def create_event_loop(self):
        return uv_events.EventLoop()


if __name__ == '__main__':
    unittest.main()
