import os
import sys
import asyncio
from .lib.protocol import _SiriDBProtocol
from .lib.protocol import _SiriDBInfoProtocol
from .lib.connection import SiriDBConnection
from .lib.defaults import DEFAULT_CLIENT_PORT
from .lib.client import SiriDBClient
from .lib.constants import SECOND
from .lib.constants import MICROSECOND
from .lib.constants import MILLISECOND
from .lib.constants import NANOSECOND

__all__ = [
    'async_connect',
    'async_server_info',
    'connect',
    'SiriDBClient',
    'SiriDBProtocol',
    'SECOND',
    'MICROSECOND',
    'MILLISECOND',
    'NANOSECOND'
]


class SiriDBProtocol(_SiriDBProtocol):

    def on_connection_made(self):
        pass

    def on_authenticated(self):
        pass

    def on_connection_lost(self, exc):
        pass


def connect(username,
            password,
            dbname,
            host='127.0.0.1',
            port=DEFAULT_CLIENT_PORT,
            loop=None,
            timeout=10,
            protocol=SiriDBProtocol):

    return SiriDBConnection(
        username,
        password,
        dbname,
        host=host,
        port=port,
        loop=loop,
        timeout=timeout,
        protocol=protocol)


async def async_connect(username,
                        password,
                        dbname,
                        host='127.0.0.1',
                        port=DEFAULT_CLIENT_PORT,
                        loop=None,
                        timeout=10,
                        keepalive=False,
                        protocol=SiriDBProtocol):

    connection = SiriDBAsyncConnection()
    await connection.connect(
        username,
        password,
        dbname,
        host=host,
        port=port,
        loop=loop,
        timeout=timeout,
        keepalive=keepalive,
        protocol=protocol)

    return connection


async def async_server_info(host='127.0.0.1',
                            port=DEFAULT_CLIENT_PORT,
                            loop=None,
                            timeout=10):
    loop = loop or asyncio.get_event_loop()
    client = loop.create_connection(
        lambda: _SiriDBInfoProtocol(None, None, None),
        host=host,
        port=port)
    transport, protocol = \
        await asyncio.wait_for(client, timeout=timeout)

    result = await protocol.future
    transport.close()
    return result
