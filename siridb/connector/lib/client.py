'''SiriDB Client

SiriDB Client for python => 3.5 using asyncio.

:copyright: 2022, Jeroen van der Heijden (Cesbit.com)
'''
import asyncio
import functools
import random
from .protocol import _SiriDBProtocol, _SiriDBConnProtocol
from .connection import SiriDBAsyncConnection
from .exceptions import ServerError
from .exceptions import PoolError
from .constants import SECOND
from .constants import MICROSECOND
from .constants import MILLISECOND
from .constants import NANOSECOND
from .protomap import CPROTO_REQ_QUERY
from .protomap import CPROTO_REQ_INSERT
from .protomap import CPROTO_REQ_PING
from .logging import logger as logging


class _SiriDBClientProtocol(_SiriDBProtocol):

    _is_available = False

    def __init__(self, *args, trigger_connect, inactive_time):
        super().__init__(*args)
        self._trigger_connect = trigger_connect
        self._inactive_time = inactive_time

    def on_authenticated(self):
        self._is_available = True

    def on_connection_lost(self, exc):
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


class SiriDBClient:
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
        - UserAuthError
            The user as no rights to perform the insert or query.
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
            client = SiriDBAsyncConnection()
            client.host = host
            client.port = port
            client.is_backup = config.get('backup', False)
            client.weight = config.get('weight', 1)
            assert 0 < client.weight < 10, \
                'weight should be value between 1 and 9'
            for _ in range(client.weight):
                self._connection_pool.append(client)
        self._connections = set(self._connection_pool)
        self._loop = loop or asyncio.get_running_loop()
        self._timeout = timeout
        self._connect_task = None
        self._max_wait_retry = max_wait_retry
        self._protocol = \
            functools.partial(_SiriDBClientProtocol,
                              trigger_connect=self._trigger_connect,
                              inactive_time=inactive_time)

    @property
    def is_closed(self):
        '''Can be used to check if close() has been called.'''
        return not self._retry_connect

    @property
    def connected(self):
        '''Can be used to check the client has any active connections'''
        return any(connection.connected for connection in self._connections)

    @staticmethod
    def _log_connect_result(result):
        for r in result:
            if r:
                msg = str(r) or type(r).__name__
                logging.error(msg)

    async def connect(self, timeout=None):
        self._retry_connect = True
        result = await self._connect(timeout)
        if result and set(result) - {None} and self._connect_task is None:
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

    async def insert(self, data, timeout=300):
        end = self._loop.time() + timeout
        while True:
            connection = self._get_random_connection()

            try:
                result = await connection.insert(data, timeout)
            except (ConnectionError, ServerError) as e:
                logging.debug('Insert failed with error {!r}, trying another '
                              'server if one is available...'.format(e))
                if connection._protocol:
                    connection._protocol.set_not_available(self._loop)
            except PoolError as e:
                if self._loop.time() > end:
                    raise
                msg = str(e) or type(e).__name__
                logging.debug(msg)
                await asyncio.sleep(2)
            else:
                return result

    async def query(self, query, time_precision=None, timeout=60):
        assert isinstance(query, (str, bytes)), \
            'query should be of type str, unicode or bytes'

        assert time_precision is None or isinstance(time_precision, int), \
            'time_precision should be None or an int type.'

        end = self._loop.time() + timeout
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
            except PoolError as e:
                if self._loop.time() > end:
                    raise
                msg = str(e) or type(e).__name__
                logging.debug(msg)
                await asyncio.sleep(2)
            else:
                return result

            # only try unavailable once
            try_unavailable = False

    async def _connect(self, timeout=None):  # the one that actually connects
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

    async def _connect_loop(self):  # the one that looks for connections
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


class SiriDBConn:

    MAX_RECONNECT_WAIT_TIME = 60
    MAX_RECONNECT_TIMEOUT = 10
    MAX_WRITE_RETRY = 120
    RECONNECT_ATTEMPT = 3

    def __init__(self,
                 username,
                 password,
                 dbname,
                 server,
                 port=9000,
                 loop=None):
        self._username = username
        self._password = password
        self._dbname = dbname
        self._server = server
        self._port = port
        self._loop = loop or asyncio.get_running_loop()
        self._reconnecting = False
        self._protocol = None

    async def _connect(self, timeout):
        client = self._loop.create_connection(
            lambda: _SiriDBConnProtocol(
                self._username,
                self._password,
                self._dbname),
            host=self._server,
            port=self._port)
        _transport, self._protocol = \
            await asyncio.wait_for(client, timeout=timeout)

        try:
            _res = await asyncio.wait_for(
                self._protocol.auth_future,
                timeout=timeout)
        except Exception as exc:
            _transport.close()
            raise exc

    async def _reconnect_loop(self):
        try:
            wait_time = 1
            timeout = 2
            protocol = self._protocol
            while True:
                host, port = self._server, self._port
                try:
                    await self._connect(timeout=timeout)
                except Exception as e:
                    logging.error(
                        f'Connecting to {host}:{port} failed: '
                        f'{e}({e.__class__.__name__}), '
                        f'Try next connect in {wait_time} seconds'
                    )
                else:
                    if protocol and protocol._connected:
                        # make sure the `old` connection will be dropped
                        self._loop.call_later(10.0, protocol.transport.close)
                    break

                await asyncio.sleep(wait_time)
                wait_time *= 2
                wait_time = min(wait_time, self.MAX_RECONNECT_WAIT_TIME)
                timeout = min(timeout+1, self.MAX_RECONNECT_TIMEOUT)
        finally:
            self._reconnecting = False

    def _reconnect(self):
        if self._reconnecting:
            return asyncio.sleep(1)
        self._reconnecting = True
        return self._reconnect_loop()

    def is_connected(self):
        return self._protocol and self._protocol._connected

    async def insert(self, data, timeout=300):
        result = await self._ensure_write(
            CPROTO_REQ_INSERT,
            data=data,
            timeout=timeout)
        return result

    def close(self):
        if self.is_connected():
            if not hasattr(self._protocol, 'close_future'):
                self._protocol.close_future = self._loop.create_future()
            self._protocol.transport.close()

    async def wait_closed(self):
        if self._protocol and hasattr(self._protocol, 'close_future'):
            await self._protocol.close_future

    async def connect(self, timeout=120):
        result = await self._ensure_write(CPROTO_REQ_PING, timeout=timeout)
        return result

    async def query(self, query, time_precision=None, timeout=60):
        assert isinstance(query, (str, bytes)), \
            'query should be of type str, unicode or bytes'
        assert time_precision in (
            None,
            SECOND,
            MICROSECOND,
            MILLISECOND,
            NANOSECOND), 'time_precision must be either None, 0, 1, 2, 3'
        result = await self._ensure_write(
            CPROTO_REQ_QUERY,
            data=(query, time_precision),
            timeout=timeout)
        return result

    async def _ensure_write(
            self,
            tipe, data=None, is_binary=False, timeout=None):
        retry = 0
        while True:
            retry += 1

            if not self.is_connected():
                if retry > self.MAX_WRITE_RETRY:
                    raise ConnectionError("Failed to create a connection")
                if retry == 1:
                    logging.info('Wait for a connection')
                await self._reconnect()  # ensure the re-connect loop
                continue

            try:
                res = await self._protocol.send_package(
                    tipe, data, is_binary, timeout)
            except (ServerError,
                    PoolError,
                    OSError,
                    asyncio.TimeoutError) as e:
                if retry > self.MAX_WRITE_RETRY:
                    raise e
                if retry % self.RECONNECT_ATTEMPT == 0:
                    await self._reconnect()
                else:
                    await asyncio.sleep(1.0)
                continue

            return res
