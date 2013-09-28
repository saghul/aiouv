
import argparse
import rose
import signal
import tulip

from tulip import protocols


loop = rose.EventLoop()


class EchoServerProtocol(protocols.Protocol):

    def connection_made(self, transport):
        print("Client connected")
        self.transport = transport

    def data_received(self, data):
        self.transport.write(data)

    def eof_received(self):
        self.transport.close()

    def connection_lost(self, exc):
        print('Connection lost:', exc)


class EchoClientProtocol(protocols.Protocol):

    def connection_made(self, transport):
        print("Connected!")
        self.transport = transport

    def data_received(self, data):
        self.transport.write(data)

    def eof_received(self):
        self.transport.close()

    def connection_lost(self, exc):
        print('Connection closed:', exc)
        loop.stop()


def start_tcp_server(host, port):
    handle = rose.listen_tcp(loop, EchoServerProtocol, (host, port))
    print('Echo TCP server listening')
    return handle


def start_tcp_client(host, port):
    t = tulip.async(rose.connect_tcp(loop, EchoClientProtocol, (host, port)), loop=loop)
    transport, protocol = loop.run_until_complete(t)
    print('Echo TCP client connected')
    return transport, protocol


def start_pipe_server(name):
    handle = rose.listen_pipe(loop, EchoServerProtocol, name)
    print('Echo Pipe server listening')
    return handle


def start_pipe_client(name):
    t = tulip.async(rose.connect_pipe(loop, EchoClientProtocol, name), loop=loop)
    transport, protocol = loop.run_until_complete(t)
    print('Echo Pipe client connected')
    return transport, protocol


parser = argparse.ArgumentParser(description='Multi-Echo example')
parser.add_argument(
    '--server', action="store_true", dest='server',
    default=False, help='Run a server')
parser.add_argument(
    '--client', action="store_true", dest='client',
    default=False, help='Run a client')
parser.add_argument(
    '--tcp', action="store_true", dest='tcp',
    default=False, help='Use TCP')
parser.add_argument(
    '--pipe', action="store_true", dest='pipe',
    default=False, help='Use named pipes')
parser.add_argument(
    'addr', action="store", 
    help='address / pipe name')


if __name__ == '__main__':
    args = parser.parse_args()
    if (args.client and args.server) or (not args.client and not args.server):
        raise RuntimeError('incorrect parameters')
    if (args.tcp and args.pipe) or (not args.tcp and not args.pipe):
        raise RuntimeError('incorrect parameters')
    
    if args.tcp:
        host, _ , port = args.addr.rpartition(':')
        host = host.strip('[]')
        port = int(port)
        if args.server:
            x = start_tcp_server(host, port)
        elif args.client:
            x = start_tcp_client(host, port)
    elif args.pipe:
        name = args.addr
        if args.server:
            x = start_pipe_server(name)
        else:
            x = start_pipe_client(name)

    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.run_forever()

