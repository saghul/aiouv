
import pyuv

from tulip import futures
from tulip import tasks
from tulip import transports
from tulip.log import tulip_log

__all__ = ['connect_tcp', 'listen_tcp', 'connect_pipe', 'listen_pipe']


class StreamTransport(transports.Transport):

    def __init__(self, loop, protocol, handle, extra=None):
        super().__init__(extra)
        self._loop = loop
        self._protocol = protocol
        self._handle = handle

        self._buffer = []
        self._closing = False
        self._shut = False
        self._write_paused = False

        self._handle.start_read(self._on_read)
        self._loop.call_soon(self._protocol.connection_made, self)

    @property
    def loop(self):
        return self._loop

    def close(self):
        if self._closing:
            return
        self._closing = True
        if self._buffer:
            assert not self._shut
            self._loop.call_soon(self._call_connection_lost, None)
            buffer, self._buffer = self._buffer, buffer
            self._handle.writelines(buffer, self._on_write)
        if not self._shut:
            self._handle.shutdown(self._on_shutdown)
        else:
            # The handle is already shut, someone called write_eof, so just
            # call connection_lost
            self._call_connection_lost(None)

    def pause(self):
        if self._closing:
            return
        self._handle.stop_read()

    def resume(self):
        if self._closing:
            return
        self._handle.start_read(self._on_read)

    def write(self, data):
        assert isinstance(data, bytes), repr(data)
        if not data:
            return
        if self._closing:
            return
        if self._write_paused:
            self._buffer.append(data)
        else:
            self._handle.write(data, self._on_write)

    def writelines(self, seq):
        if not seq:
            return
        if self._closing:
            return
        if self._write_paused:
            self._buffer.extend(seq)
        else:
            self._handle.writelines(seq, self._on_write)

    def write_eof(self):
        # TODO: add shutting flag to prevent this from being called multiple times
        if self._closing:
            return
        self._handle.shutdown(self._on_shutdown)

    def can_write_eof(self):
        return True

    def pause_writing(self):
        self._write_paused = True

    def resume_writing(self):
        self._write_paused = False
        if not self._closing and self._buffer:
            buffer, self._buffer = self._buffer, []
            self._handle.writelines(buffer)

    def discard_output(self):
        self._buffer.clear()

    def abort(self):
        self._close(None)

    def _close(self, exc):
        if self._closing:
            return
        self._closing = True
        self._buffer.clear()
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
                tulip_log.warning('error reading from TCP connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
                exc = ConnectionError(error, pyuv.errno.strerror(error))
                self._close(exc)
        else:
            self._protocol.data_received(data)

    def _on_write(self, handle, error):
        if error is not None:
            tulip_log.warning('error writing to TCP connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
            exc = ConnectionError(error, pyuv.errno.strerror(error))
            self._close(exc)
            return

    def _on_shutdown(self, handle, error):
        self._shut = True
        if self._closing:
            self._call_connection_lost(None)


## Some extra functions for using the extra transports provided by rose

class TCPTransport(StreamTransport):
    pass


def _tcp_listen_cb(server, error):
    if error is not None:
        tulip_log.warning('error processing incoming TCP connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    conn = pyuv.TCP(server.loop)
    try:
        server.accept(conn)
    except pyuv.error.TCPError as e:
        error = e.args[0]
        tulip_log.warning('error accepting incoming TCP connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    addr = conn.getpeername()
    return TCPTransport(conn.loop._rose_loop, server.protocol_factory(), conn, extra={'addr': addr})


def listen_tcp(loop, protocol_factory, addr):
    handle = pyuv.TCP(loop._loop)
    handle.bind(addr)
    handle.listen(_tcp_listen_cb)
    handle.protocol_factory = protocol_factory
    return handle


def _tcp_connect_cb(handle, error):
    if error is not None:
        handle.waiter.set_exception(ConnectionError(error, pyuv.errno.strerror(error)))
    else:
        handle.waiter.set_result(None)


@tasks.coroutine
def connect_tcp(loop, protocol_factory, addr, bindaddr=None):
    protocol = protocol_factory()
    waiter = futures.Future(loop=loop)

    handle = pyuv.TCP(loop._loop)
    if bindaddr is not None:
        handle.bind((interface, port))
    handle.connect(addr, _tcp_connect_cb)
    handle.waiter = waiter

    yield from waiter

    addr = handle.getpeername()
    transport = TCPTransport(loop, protocol, handle, extra={'addr': addr})
    return transport, protocol


class PipeTransport(StreamTransport):
    pass


def _pipe_listen_cb(server, error):
    if error is not None:
        tulip_log.warning('error processing incoming Pipe connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    conn = pyuv.Pipe(server.loop)
    try:
        server.accept(conn)
    except pyuv.error.PipeError as e:
        error = e.args[0]
        tulip_log.warning('error accepting incoming Pipe connection: {} - {}'.format(error, pyuv.errno.strerror(error)))
        return
    return PipeTransport(conn.loop._rose_loop, server.protocol_factory(), conn)


def listen_pipe(loop, protocol_factory, name):
    handle = pyuv.Pipe(loop._loop)
    handle.bind(name)
    handle.listen(_pipe_listen_cb)
    handle.protocol_factory = protocol_factory
    return handle


def _pipe_connect_cb(handle, error):
    if error is not None:
        handle.waiter.set_exception(ConnectionError(error, pyuv.errno.strerror(error)))
    else:
        handle.waiter.set_result(None)


@tasks.coroutine
def connect_pipe(loop, protocol_factory, name):
    protocol = protocol_factory()
    waiter = futures.Future(loop=loop)

    handle = pyuv.Pipe(loop._loop)
    handle.connect(name, _pipe_connect_cb)
    handle.waiter = waiter

    yield from waiter

    transport = PipeTransport(loop, protocol, handle)
    return transport, protocol

