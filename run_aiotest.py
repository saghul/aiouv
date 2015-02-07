import aiotest.run
import asyncio
import rose
import sys
if sys.platform == 'win32':
    from asyncio.windows_utils import socketpair
else:
    from socket import socketpair

config = aiotest.TestConfig()
config.asyncio = rose
config.socketpair = socketpair
config.new_event_pool_policy = rose.EventLoopPolicy
config.call_soon_check_closed = True
aiotest.run.main(config)
