import os
import sys
import asyncio
from .lib.protocol import _SiriDBProtocol
from .lib.connection import SiriDBConnection
from .lib.defaults import DEFAULT_CLIENT_PORT
from .lib.client import SiriDBClient
from .lib.constants import SECOND
from .lib.constants import MICROSECOND
from .lib.constants import MILLISECOND
from .lib.constants import NANOSECOND


__version_info__ = (2, 0, 6)
__version__ = '.'.join(map(str, __version_info__))
__maintainer__ = 'Jeroen van der Heijden'
__email__ = 'jeroen@transceptor.technology'
__all__ = [
    'async_connect',
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
