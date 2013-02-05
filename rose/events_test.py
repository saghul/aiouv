
import socket
import unittest

from tulip import test_utils
from tulip import events_test

from rose import uv_events


class RoseEventLoopTests(events_test.EventLoopTestsMixin, test_utils.LogTrackingTestCase):
    def create_event_loop(self):
        return uv_events.EventLoop()

    @unittest.mock.patch('rose.uv_events.socket')
    def test_start_serving_cant_bind(self, m_socket):
        class Err(socket.error):
            pass

        m_socket.error = socket.error
        m_socket.getaddrinfo.return_value = [(2, 1, 6, '', ('127.0.0.1',10100))]
        m_sock = m_socket.socket.return_value = unittest.mock.Mock()
        m_sock.setsockopt.side_effect = Err

        fut = self.event_loop.start_serving(events_test.MyProto, '0.0.0.0', 0)
        self.assertRaises(Err, self.event_loop.run_until_complete, fut)
        self.assertTrue(m_sock.close.called)


if __name__ == '__main__':
    unittest.main()
