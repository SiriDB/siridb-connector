import os
import sys
from .lib.protocol import _SiriDBClientProtocol
from .lib.connection import SiriDBConnection


class SiriDBClientProtocol(_SiriClientProtocol):

    def on_connection_made(self):
        pass

    def on_authenticated(self):
        pass

    def on_connection_lost(self):
        pass


def connect(username,
            password,
            dbname,
            host='127.0.0.1',
            port=c.DEFAULT_CLIENT_PORT,
            loop=None,
            timeout=10,
            protocol=SiriClientProtocol):

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
                        port=c.DEFAULT_CLIENT_PORT,
                        loop=None,
                        timeout=10,
                        keepalive=False,
                        protocol=SiriClientProtocol):

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



__all__ = [
    'connect',
    'async_connect',
    'SiriDBClientProtocol']
