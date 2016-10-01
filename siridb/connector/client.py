'''SiriDB Client

SiriDB Client for python => 3.5 using asyncio.

Note: for a python 2.7 SiriDB client we have another client running on Twisted.

:copyright: 2016, Jeroen van der Heijden (Transceptor Technology)
'''
import asyncio
import random
import logging
import functools
import time
from .shared.packageprotocol import networkpackets as npt
from .shared import constants as c
from .shared.exceptions import ServerError
from .shared.exceptions import PoolError
from .shared.exceptions import AuthenticationError
from .shared.exceptions import UserAuthError
from .shared.exceptions import NetworkAuthError
from .protocol import SiriClientProtocol as _SiriClientProtocol
from .protocol import PackageClientProtocol


class SiriClientProtocol(_SiriClientProtocol):

    def on_connection_made(self):
        pass

    def on_authenticated(self):
        pass

    def on_connection_lost(self):
        pass


class SiriClient():

    def connect(self,
                username,
                password,
                dbname,
                host='127.0.0.1',
                port=c.DEFAULT_CLIENT_PORT,
                loop=None,
                timeout=10,
                protocol=SiriClientProtocol):
        self._loop = loop or asyncio.get_event_loop()
        client = self._loop.create_connection(
            lambda: protocol(username, password, dbname),
            host=host,
            port=port)
        self._transport, self._protocol = self._loop.run_until_complete(
            asyncio.wait_for(client, timeout=timeout))
        self._loop.run_until_complete(self._protocol.auth_future)

    def close(self):
        if hasattr(self, '_protocol') and hasattr(self._protocol, 'transport'):
            self._protocol.transport.close()

    def query(self, query, time_precision=None, timeout=30):
        result = self._loop.run_until_complete(
            self._protocol.send_package(npt.CPROTO_REQ_QUERY,
                                        data=(query, time_precision),
                                        timeout=timeout))
        return result

    def insert(self, data, timeout=600):
        result = self._loop.run_until_complete(
            self._protocol.send_package(npt.CPROTO_REQ_INSERT,
                                        data=data,
                                        timeout=timeout))
        return result

    def _register_server(self, server, timeout=30):
        result = self._loop.run_until_complete(
            self._protocol.send_package(npt.CPROTO_REQ_REGISTER_SERVER,
                                        data=server,
                                        timeout=timeout))
        return result

    def _get_file(self, fn, timeout=30):
        msg = npt.FILE_MAP.get(fn, None)
        if msg is None:
            raise FileNotFoundError('Cannot get file {!r}. Available file '
                                    'requests are: {}'
                                    .format(fn, ', '.join(npt.FILE_MAP.keys())))
        result = self._loop.run_until_complete(
            self._protocol.send_package(msg, timeout=timeout))
        return result


class AsyncSiriClient():

    _protocol = None
    _keepalive = None

    async def keepalive_loop(self, interval=45):
        sleep = interval
        while True:
            await asyncio.sleep(sleep)
            if not self.connected:
                break
            sleep = \
                max(0, interval - time.time() + self._last_resp) or interval
            if sleep == interval:
                logging.debug('Send keep-alive package...')
                try:
                    await self._protocol.send_package(npt.CPROTO_REQ_PING,
                                                      timeout=15)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logging.error(e)
                    self.close()
                    break

    async def connect(self,
                      username,
                      password,
                      dbname,
                      host='127.0.0.1',
                      port=c.DEFAULT_CLIENT_PORT,
                      loop=None,
                      timeout=10,
                      keepalive=False,
                      protocol=SiriClientProtocol):
        loop = loop or asyncio.get_event_loop()
        client = loop.create_connection(
            lambda: protocol(username, password, dbname),
            host=host,
            port=port)
        self._timeout = timeout
        _transport, self._protocol = \
            await asyncio.wait_for(client, timeout=timeout)
        await self._protocol.auth_future
        self._last_resp = time.time()
        if keepalive and (self._keepalive is None or self._keepalive.done()):
            self._keepalive = asyncio.ensure_future(self.keepalive_loop())

    def close(self):
        if self._keepalive is not None:
            self._keepalive.cancel()
            del self._keepalive
        if self._protocol is not None:
            self._protocol.transport.close()
            del self._protocol

    async def query(self, query, time_precision=None, timeout=3600):
        result = await self._protocol.send_package(
            npt.CPROTO_REQ_QUERY,
            data=(query, time_precision),
            timeout=timeout)
        self._last_resp = time.time()
        return result

    async def insert(self, data, timeout=3600):
        result = await self._protocol.send_package(
            npt.CPROTO_REQ_INSERT,
            data=data,
            timeout=timeout)
        self._last_resp = time.time()
        return result

    @property
    def connected(self):
        return self._protocol is not None and self._protocol._connected


class _SiriClientInfoProtocol(_SiriClientProtocol):

    _info = []

    def connection_made(self, transport):
        def finished(future):
            if not future.exception():
                self.on_info(future.result())

        self._connected = True
        PackageClientProtocol.connection_made(self, transport)
        self.auth_future = self.send_package(npt.CPROTO_REQ_INFO,
                                             data=None,
                                             timeout=10)
        self.auth_future.add_done_callback(finished)
        self._password = None
        self.on_connection_made()

    def on_info(self, data):
        self._info = data


async def get_siridb_info(host='127.0.0.1',
                          port=c.DEFAULT_CLIENT_PORT,
                          loop=None,
                          timeout=10,
                          protocol=_SiriClientInfoProtocol):
    loop = loop or asyncio.get_event_loop()
    client = loop.create_connection(
        lambda: protocol(None, None, None),
        host=host,
        port=port)
    transport, protocol = \
        await asyncio.wait_for(client, timeout=timeout)
    await protocol.auth_future
    transport.close()
    return protocol._info


class _SiriClientLoadDBProtocol(_SiriClientProtocol):

    def connection_made(self, transport):
        def finished(future):
            pass

        self._connected = True
        PackageClientProtocol.connection_made(self, transport)
        self.auth_future = self.send_package(npt.CPROTO_REQ_LOADDB,
                                             data=self._dbname,
                                             timeout=10)
        self.auth_future.add_done_callback(finished)
        self._password = None
        self.on_connection_made()


async def load_database(dbpath,
                        host='127.0.0.1',
                        port=c.DEFAULT_CLIENT_PORT,
                        loop=None,
                        timeout=10,
                        protocol=_SiriClientLoadDBProtocol):
    loop = loop or asyncio.get_event_loop()
    client = loop.create_connection(
        lambda: protocol(None, None, dbpath),
        host=host,
        port=port)
    transport, protocol = \
        await asyncio.wait_for(client, timeout=timeout)
    await protocol.auth_future
    transport.close()


class SiriClusterProtocol(_SiriClientProtocol):

    _is_available = False

    def __init__(self, *args, trigger_connect, inactive_time):
        super().__init__(*args)
        self._trigger_connect = trigger_connect
        self._inactive_time = inactive_time

    def on_authenticated(self):
        self._is_available = True

    def on_connection_lost(self):
        self._is_available = False
        self._trigger_connect()

    def set_available(self):
        if self._connected:
            self._is_available = True

    def set_not_available(self, loop):
        if self._is_available:
            self._is_available = False
            loop.call_later(self._inactive_time, self.set_available)


# never wait more than x seconds before trying to connect again
DEFAULT_MAX_WAIT_RETRY = 90

# default timeout used while connecting to a SiriDB server
DEFAULT_CONNECT_TIMEOUT = 10

# when a SiriDB server is marked as inactive, wait x seconds before releasing
# the inactive status.
DEFAULT_INACTIVE_TIME = 30


class AsyncSiriCluster:
    '''
        Exception handling:

        - InsertError (can only be raised when using the insert() method)
            Make sure the data is correct because this only happens when
            SiriDB could not process the request. Its likely to fail again
            on a retry.
        - QueryError (can only be raised when using the query() method)
            Make sure the query is correct because this only happens when
            SiriDB could not process the query. Its likely to fail again.
        - PoolError
            SiriDB has no online server for at least one required pool
            Try again later after some reasonable delay.
        - AuthenticationError
            Raised when credentials are invalid or insufficient
        - IndexError
            Raised when the database does not exist (anymore)
        - TypeError
            Raised when an unknown package is received. (might be caused
            by running a different SiriDB version)
        - RuntimeError
            Raised when a general error message is received. This should not
            happen unless a new bug is discovered.
        - OverflowError (can only be raised when using the insert() method)
            Raise when integer values cannot not be packed due to an overflow
            error. (integer values should be signed and not more than 63 bits)
    '''

    def __init__(self,
                 username,
                 password,
                 dbname,
                 hostlist,
                 loop=None,
                 keepalive=True,
                 timeout=DEFAULT_CONNECT_TIMEOUT,
                 inactive_time=DEFAULT_INACTIVE_TIME,
                 max_wait_retry=DEFAULT_MAX_WAIT_RETRY):
        '''Initialize.
        Arguments:
            username: User with permissions to use the database.
            password: Password for the given username.
            dbname: Name of the database.
            hostlist: List with SiriDB servers. (all servers or a subset of
                      servers can be in this list.)

                      Example:
                      [
                          ('server1.local', 9000, {'weight': 3}),
                          ('server2.local', 9000),
                          ('backup1.local', 9000, {'backup': True})
                      ]

                      Each server should at least has a hostname and port
                      number. Optionally you can provide a dictionary with
                      extra options.

                      Available Options:
                      - weight : Should be a value between 1 and 9. A higher
                                 value gives the server more weight so it will
                                 be more likely chosen. (default 1)
                      - backup : Should be either True or False. When True the
                                 server will be marked as backup server and
                                 will only be chosen if no other server is
                                 available. (default: False)

        Keyword arguments:
            loop: Asyncio loop. When None the default event loop will be used.
            keepalive: SiriDB Version >= 0.9.35 supporting keep-alive packages
            timeout: Timeout used when reconnecting to a SiriDB server.
            inactive_time: When a server is temporary not available, for
                           example the server could be paused, we mark the
                           server inactive for x seconds.
            max_wait_retry: When the reconnect loop starts, we try to reconnect
                            in a seconds, then 2 seconds, 4, 8 and so on until
                            max_wait_retry is reached and then use this value
                            to retry again.
        '''
        self._username = username
        self._password = password
        self._dbname = dbname
        self._connection_pool = []
        self._keepalive = keepalive
        for host, port, *config in hostlist:
            config = config.pop() if config else {}
            client = AsyncSiriClient()
            client.host = host
            client.port = port
            client.is_backup = config.get('backup', False)
            client.weight = config.get('weight', 1)
            assert 0 < client.weight < 10, \
                'weight should be value between 1 and 9'
            for _ in range(client.weight):
                self._connection_pool.append(client)
        self._connections = set(self._connection_pool)
        self._loop = loop or asyncio.get_event_loop()
        self._timeout = timeout
        self._connect_task = None
        self._max_wait_retry = max_wait_retry
        self._protocol = \
            functools.partial(SiriClusterProtocol,
                              trigger_connect=self._trigger_connect,
                              inactive_time=inactive_time)

    @staticmethod
    def _log_connect_result(result):
        for r in result:
            if r:
                logging.error(r)
                if isinstance(r, (IndexError, AuthenticationError)):
                    break

    async def connect(self, timeout=None):
        self._retry_connect = True
        result = await self._connect(timeout)
        if result and set(result) - {None}:
            self._connect_task = asyncio.ensure_future(self._connect_loop())
        return result

    def close(self):
        self._retry_connect = False
        if self._connect_task is not None:
            self._connect_task.cancel()
            self._connect_task = None
        for connection in self._connections:
            if connection.connected:
                connection.close()

    async def insert(self, data, timeout=3600):
        while True:
            connection = self._get_random_connection()

            try:
                result = await connection.insert(data, timeout)
            except (ConnectionError, ServerError) as e:
                logging.debug('Insert failed with error {!r}, trying another '
                              'server if one is available...'.format(e))
                if connection._protocol:
                    connection._protocol.set_not_available(self._loop)
            else:
                return result

    async def query(self, query, time_precision=None, timeout=3600):
        try_unavailable = True
        while True:
            connection = self._get_random_connection(try_unavailable)
            try:
                result = await connection.query(query,
                                                time_precision=time_precision,
                                                timeout=timeout)
            except (ConnectionError, ServerError) as e:
                logging.debug('Query failed with error {!r}, trying another '
                              'server if one is available...'.format(e))
                if connection._protocol:
                    connection._protocol.set_not_available(self._loop)
            else:
                return result

            # only try unavailable once
            try_unavailable = False

    async def _connect(self, timeout=None):
        tasks = [
            connection.connect(
                self._username,
                self._password,
                self._dbname,
                host=connection.host,
                port=connection.port,
                loop=self._loop,
                keepalive=self._keepalive,
                timeout=timeout or self._timeout,
                protocol=self._protocol)
            for connection in self._connections
            if not connection.connected]
        if not tasks:
            return
        logging.debug('Trying to connect to {} servers...'
                      .format(len(tasks)))
        result = await asyncio.gather(*tasks, return_exceptions=True)
        self._log_connect_result(result)
        return result

    async def _connect_loop(self):
        sleep = 1
        try:
            while [connection
                   for connection in self._connections
                   if not connection.connected]:
                logging.debug('Reconnecting in {} seconds...'.format(sleep))
                await asyncio.sleep(sleep)
                if self._connect_task is None:
                    break
                await self._connect()
                if self._connect_task is None:
                    break
                sleep = min(sleep * 2, self._max_wait_retry)
        except asyncio.CancelledError:
            pass
        finally:
            self._connect_task = None

    def _trigger_connect(self):
        if self._retry_connect and self._connect_task is None:
            self._connect_task = asyncio.ensure_future(self._connect_loop())

    def _get_random_connection(self, try_unavailable=False):
        available = \
            [connection
             for connection in self._connection_pool
             if connection._protocol and connection._protocol._is_available]

        non_backups = \
            [connection
             for connection in available
             if not connection.is_backup]

        if non_backups:
            return random.choice(non_backups)

        if available:
            return random.choice(available)

        if try_unavailable:

            connections = \
                [connection
                 for connection in self._connection_pool
                 if connection.connected]

            if connections:
                return random.choice(connections)

        raise PoolError('No available connections found')
