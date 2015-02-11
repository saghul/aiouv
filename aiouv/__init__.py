
import asyncio

from ._events import EventLoop
from ._transports import connect_tcp, listen_tcp, connect_pipe, listen_pipe, create_udp_endpoint

__all__ = ['EventLoopPolicy', 'EventLoop',
           'connect_tcp', 'listen_tcp',
           'connect_pipe', 'listen_pipe',
           'create_udp_endpoint']


class EventLoopPolicy(asyncio.events.BaseDefaultEventLoopPolicy):
    """In this policy, each thread has its own event loop."""

    _loop_factory = EventLoop