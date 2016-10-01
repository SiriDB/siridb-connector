import os
import sys
from .client import (
    SiriClient,
    SiriClientProtocol,
    AsyncSiriClient,
    AsyncSiriCluster)

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

    connection = SiriDBConnection(loop)


    client = self._loop.create_connection(
        lambda: protocol(username, password, dbname),
        host=host,
        port=port)

    self._transport, self._protocol = self._loop.run_until_complete(
        asyncio.wait_for(client, timeout=timeout))
    self._loop.run_until_complete(self._protocol.auth_future)

__all__ = ['SiriClient',
           'SiriClientProtocol',
           'AsyncSiriClient',
           'AsyncSiriCluster']
