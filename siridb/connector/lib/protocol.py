'''SiriDB Client protocol

:copyright: 2022, Jeroen van der Heijden (Cesbit.com)
'''
import asyncio
import qpack
from . import protomap
from .datapackage import DataPackage
from .exceptions import InsertError
from .exceptions import QueryError
from .exceptions import ServerError
from .exceptions import PoolError
from .exceptions import AuthenticationError
from .exceptions import UserAuthError
from .logging import logger as logging


_MAP = (
    lambda data: b'',
    lambda data: qpack.packb(data),
    lambda data: data
)


def _packdata(tipe, data=None):
    assert tipe in protomap.MAP_REQ_DTYPE, \
        'No data type found for message type: {}'.format(tipe)
    return _MAP[protomap.MAP_REQ_DTYPE[tipe]](data)


class _SiriDBProtocol(asyncio.Protocol):

    _connected = False

    _MAP = {
        # SiriDB Client protocol success response types
        protomap.CPROTO_RES_QUERY: lambda f, d: f.set_result(d),
        protomap.CPROTO_RES_INSERT: lambda f, d: f.set_result(d),
        protomap.CPROTO_RES_ACK: lambda f, d: f.set_result(None),
        protomap.CPROTO_RES_AUTH_SUCCESS: lambda f, d: f.set_result(True),
        protomap.CPROTO_RES_INFO: lambda f, d: f.set_result(d),
        protomap.CPROTO_RES_FILE: lambda f, d: f.set_result(d),

        # SiriDB Client protocol error response types
        protomap.CPROTO_ERR_MSG: lambda f, d: f.set_exception(
            RuntimeError(d.get('error_msg', None))),
        protomap.CPROTO_ERR_QUERY: lambda f, d: f.set_exception(
            QueryError(d.get('error_msg', None))),
        protomap.CPROTO_ERR_INSERT: lambda f, d: f.set_exception(
            InsertError(d.get('error_msg', None))),
        protomap.CPROTO_ERR_SERVER: lambda f, d: f.set_exception(
            ServerError(d.get('error_msg', None))),
        protomap.CPROTO_ERR_POOL: lambda f, d: f.set_exception(
            PoolError(d.get('error_msg', None))),
        protomap.CPROTO_ERR_USER_ACCESS: lambda f, d: f.set_exception(
            UserAuthError(d.get('error_msg', None))),
        protomap.CPROTO_ERR: lambda f, d: f.set_exception(
            RuntimeError(
                'Unexpected error occurred, view siridb log '
                'for more info')),
        protomap.CPROTO_ERR_NOT_AUTHENTICATED: lambda f, d: f.set_exception(
            AuthenticationError('This connection is not authenticated')),
        protomap.CPROTO_ERR_AUTH_CREDENTIALS: lambda f, d: f.set_exception(
            AuthenticationError('Invalid credentials')),
        protomap.CPROTO_ERR_AUTH_UNKNOWN_DB: lambda f, d: f.set_exception(
            AuthenticationError('Unknown database')),
        protomap.CPROTO_ERR_LOADING_DB: lambda f, d: f.set_exception(
            RuntimeError(
                'Error loading database, '
                'please check the SiriDB log files')),
        protomap.CPROTO_ERR_FILE: lambda f, d: f.set_exception(
            RuntimeError('Error retreiving file')),
    }

    def __init__(self, username, password, dbname):
        self._buffered_data = bytearray()
        self._data_package = None
        self._pid = 0
        self._requests = {}
        self._username = username
        self._password = password
        self._dbname = dbname
        self.auth_future = None

    def connection_made(self, transport):
        '''
        override asyncio.Protocol
        '''

        self._connected = True
        self.transport = transport

        self.remote_ip, self.port = transport.get_extra_info('peername')[:2]

        logging.debug(
            'Connection made (address: {} port: {})'
            .format(self.remote_ip, self.port))

        self.auth_future = self.send_package(protomap.CPROTO_REQ_AUTH,
                                             data=(self._username,
                                                   self._password,
                                                   self._dbname),
                                             timeout=10)

        self._password = None
        self.on_connection_made()

    def connection_lost(self, exc):
        '''
        override asyncio.Protocol
        '''
        self._connected = False

        logging.debug(
            'Connection lost (address: {} port: {})'
            .format(self.remote_ip, self.port))

        for pid, (future, task) in self._requests.items():
            task.cancel()
            if future.cancelled():
                continue
            future.set_exception(ConnectionError(
                'Connection is lost before we had an answer on package id: {}.'
                .format(pid)))

        self.on_connection_lost(exc)

    def data_received(self, data):
        '''
        override asyncio.Protocol
        '''
        self._buffered_data.extend(data)
        while self._buffered_data:
            size = len(self._buffered_data)
            if self._data_package is None:
                if size < DataPackage.struct_datapackage.size:
                    return None
                self._data_package = DataPackage(self._buffered_data)
            if size < self._data_package.length:
                return None
            try:
                self._data_package.extract_data_from(self._buffered_data)
            except KeyError as e:
                logging.error('Unsupported package received: {}'.format(e))
            except Exception as e:
                logging.exception(e)
                # empty the byte-array to recover from this error
                self._buffered_data.clear()
            else:
                self._on_package_received()
            self._data_package = None

    def send_package(self, tipe, data=None, is_binary=False, timeout=3600):
        self._pid += 1
        self._pid %= 65536  # pid is handled as uint16_t

        if not is_binary:
            data = _packdata(tipe, data)

        header = DataPackage.struct_datapackage.pack(
            len(data),
            self._pid,
            tipe,
            tipe ^ 255)

        self.transport.write(header + data)

        task = asyncio.ensure_future(self._timeout_request(self._pid,
                                                           timeout,
                                                           tipe))
        future = asyncio.Future()
        self._requests[self._pid] = (future, task)
        return future

    def on_connection_made(self):
        '''
        Called when a connection is made.
        The connection might not be useful until authentication has finished.
        '''
        pass

    def on_authenticated(self):
        '''
        Called when the connection is authenticated.
        '''
        pass

    def on_connection_lost(self, exc):
        '''
        Called when the connection is lost or closed.

        The argument is an exception object or None (the latter
        meaning a regular EOF is received or the connection was
        aborted or closed).
        '''
        pass

    async def _timeout_request(self, pid, timeout, tipe):
        await asyncio.sleep(timeout)
        if not self._requests[pid][0].cancelled():
            self._requests[pid][0].set_exception(TimeoutError(
                'Request timed out on PID {} ({})'
                .format(pid, protomap.TEXT_REQ_MAP.get(tipe, 'UNKNOWN'))))
        del self._requests[pid]

    def _on_package_received(self):
        try:
            future, task = self._requests.pop(self._data_package.pid)
        except KeyError:
            logging.error(
                'Package ID not found: {} ({})'.format(
                    self._data_package.pid,
                    protomap.TEXT_RES_MAP.get(
                        self._data_package.tipe,
                        'UNKNOWN')))
            return None

        # cancel the timeout task
        task.cancel()

        if future.cancelled():
            return

        self._MAP.get(self._data_package.tipe, lambda f, d: f.set_exception(
            TypeError(
                'Client received an unknown package type: {}'
                .format(self._data_package.tipe))))(
                    future,
                    self._data_package.data)


class _SiriDBInfoProtocol(_SiriDBProtocol):

    def connection_made(self, transport):
        '''
        override _SiriDBProtocol
        '''

        self.transport = transport
        self.remote_ip, self.port = transport.get_extra_info('peername')[:2]

        logging.debug(
            'Connection made (address: {} port: {})'
            .format(self.remote_ip, self.port))

        self.future = self.send_package(
                protomap.CPROTO_REQ_INFO,
                data=None,
                timeout=10)
