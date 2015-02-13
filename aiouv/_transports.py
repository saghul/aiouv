
import pyuv

from asyncio import futures
from asyncio import tasks
from asyncio import transports
from asyncio.log import logger

__all__ = ['connect_tcp', 'listen_tcp',
           'connect_pipe', 'listen_pipe',
           'create_udp_endpoint']


class StreamTransport(transports.Transport):

    def __init__(self, loop, protocol, handle, extra=None):
        super().__init__(extra)
        self._loop = loop
        self._protocol = protocol
        self._handle = handle

        self._closing = False
        self._shutting = False

        self._handle.start_read(self._on_read)
        self._loop.call_soon(self._protocol.connection_made, self)

    @property
    def loop(self):
        return self._loop

    def close(self):
        if self._closing:
            return
        self._closing = True
        if not self._shutting:
            self._handle.shutdown(self._on_shutdown)
        else:
            # The handle is already shut, someone called write_eof, so just
            # call connection_lost
            self._call_connection_lost(None)

    def pause_reasing(self):
        if self._closing:
            return
        self._handle.stop_read()

    def resume_reading(self):
        if self._closing:
            return
        self._handle.start_read(self._on_read)

    def write(self, data):
        assert isinstance(data, bytes), repr(data)
        assert not self._shutting, 'Cannot call write() after write_eof()'
        if not data:
            return
        if self._closing:
            return
        self._handle.write(data, self._on_write)

    def writelines(self, seq):
        assert not self._shutting, 'Cannot call writelines() after write_eof()'
        if not seq:
            return
        if self._closing:
            return
        self._handle.writelines(seq, self._on_write)

    def write_eof(self):
        if self._shutting or self._closing:
            return
        self._shutting = True
        self._handle.shutdown(self._on_shutdown)

    def can_write_eof(self):
        return True

    def abort(self):
        self._close(None)

    def _close(self, exc):
        if self._closing:
            return
        self._closing = True
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        try:
            self._protocol.connection_lost(exc)
        finally:
            self._handle.close()
            self._handle = None
            self._protocol = None
            self._loop = None

    def _on_read(self, handle, data, error):
        if error is not None:
            if error == pyuv.errno.UV_EOF:
                # connection closed by remote
                try:
                    self._protocol.eof_received()
                finally:
                    self.close()
            else:
                logger.warning('error reading from connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
                exc = ConnectionError(error, pyuv.errno.strerror(error))
                self._close(exc)
        else:
            self._protocol.data_received(data)

    def _on_write(self, handle, error):
        if error is not None:
            logger.warning('error writing to connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
            exc = ConnectionError(error, pyuv.errno.strerror(error))
            self._close(exc)
            return

    def _on_shutdown(self, handle, error):
        pass


class UDPTransport(transports.DatagramTransport):

    def __init__(self, loop, protocol, handle, addr, extra=None):
        super().__init__(extra)
        self._loop = loop
        self._protocol = protocol
        self._handle = handle

        self._addr = addr
        self._closing = False

        self._handle.start_recv(self._on_recv)
        self._loop.call_soon(self._protocol.connection_made, self)

    @property
    def loop(self):
        return self._loop

    def sendto(self, data, addr=None):
        assert isinstance(data, bytes), repr(data)
        if not data:
            return
        if self._closing:
            return
        if self._addr:
            assert addr in (None, self._addr)
        self._handle.send(addr or self._addr, data, self._on_send)

    def abort(self):
        self._close(None)

    def close(self):
        if self._closing:
            return
        self._closing = True
        self._call_connection_lost(None)

    def _call_connection_lost(self, exc):
        try:
            self._protocol.connection_lost(exc)
        finally:
            self._handle.close()
            self._handle = None
            self._protocol = None
            self._loop = None

    def _close(self, exc):
        if self._closing:
            return
        self._closing = True
        if self._addr and exc and exc.args[0] == pyuv.errno.UV_ECONNREFUSED:
            self._protocol.connection_refused(exc)
        self._loop.call_soon(self._call_connection_lost, exc)

    def _on_recv(self, handle, addr, flags, data, error):
        if error is not None:
            logger.warning('error reading from UDP endpoint: {} - {}'.format(error, pyuv.errno.strerror(error)))
            exc = ConnectionError(error, pyuv.errno.strerror(error))
            self._close(exc)
        else:
            self._protocol.datagram_received(data, addr)

    def _on_send(self, handle, error):
        if error is not None:
            logger.warning('error sending to UDP endpoint: {} - {}'.format(error, pyuv.errno.strerror(error)))
            exc = ConnectionError(error, pyuv.errno.strerror(error))
            self._close(exc)


## Some extra functions for using the extra transports provided by rose

class TCPTransport(StreamTransport):
    pass


def _tcp_listen_cb(server, error):
    if error is not None:
        logger.warning('error processing incoming TCP connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    conn = pyuv.TCP(server.loop)
    try:
        server.accept(conn)
    except pyuv.error.TCPError as e:
        error = e.args[0]
        logger.warning('error accepting incoming TCP connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    addr = conn.getpeername()
    return TCPTransport(conn.loop._rose_loop, server.protocol_factory(), conn, extra={'peername': addr})


def listen_tcp(loop, protocol_factory, addr):
    handle = pyuv.TCP(loop._loop)
    handle.bind(addr)
    handle.listen(_tcp_listen_cb)
    handle.protocol_factory = protocol_factory
    return handle


@tasks.coroutine
def connect_tcp(loop, protocol_factory, addr, bindaddr=None):
    protocol = protocol_factory()
    waiter = futures.Future(loop=loop)

    def connect_cb(handle, error):
        if error is not None:
            waiter.set_exception(ConnectionError(error, pyuv.errno.strerror(error)))
        else:
            waiter.set_result(None)

    handle = pyuv.TCP(loop._loop)
    if bindaddr is not None:
        handle.bind((interface, port))
    handle.connect(addr, connect_cb)

    yield from waiter

    addr = handle.getpeername()
    transport = TCPTransport(loop, protocol, handle, extra={'peername': addr})
    return transport, protocol


class PipeTransport(StreamTransport):
    pass


def _pipe_listen_cb(server, error):
    if error is not None:
        logger.warning('error processing incoming Pipe connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    conn = pyuv.Pipe(server.loop)
    try:
        server.accept(conn)
    except pyuv.error.PipeError as e:
        error = e.args[0]
        logger.warning('error accepting incoming Pipe connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    return PipeTransport(conn.loop._rose_loop, server.protocol_factory(), conn)


def listen_pipe(loop, protocol_factory, name):
    handle = pyuv.Pipe(loop._loop)
    handle.bind(name)
    handle.listen(_pipe_listen_cb)
    handle.protocol_factory = protocol_factory
    return handle


@tasks.coroutine
def connect_pipe(loop, protocol_factory, name):
    protocol = protocol_factory()
    waiter = futures.Future(loop=loop)

    def connect_cb(handle, error):
        if error is not None:
            waiter.set_exception(ConnectionError(error, pyuv.errno.strerror(error)))
        else:
            waiter.set_result(None)

    handle = pyuv.Pipe(loop._loop)
    handle.connect(name, connect_cb)

    yield from waiter

    transport = PipeTransport(loop, protocol, handle)
    return transport, protocol


def create_udp_endpoint(loop, protocol_factory, local_addr=None, remote_addr=None):
    if not (local_addr or remote_addr):
        raise ValueError('local or remote address must be specified')
    handle = pyuv.UDP(loop._loop)
    handle.bind(local_addr or ('', 0))
    protocol = protocol_factory()
    addr = handle.getsockname()
    transport = UDPTransport(loop, protocol, handle, remote_addr, extra={'sockname': addr})
    return transport, protocol

