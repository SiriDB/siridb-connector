'''SiriDB Client protocol

:copyright: 2016, Jeroen van der Heijden (Transceptor Technology)
'''
from .shared.packageprotocol.packageprotocol import PackageClientProtocol
from .shared.packageprotocol import networkpackets as npt
from .shared.exceptions import (
    InsertError,
    QueryError,
    ServerError,
    PoolError,
    AuthenticationError,
    UserAuthError)


class SiriClientProtocol(PackageClientProtocol):

    _connected = False

    _MAP = {
        # SiriDB Client protocol success response types
        npt.CPROTO_RES_QUERY: lambda f, d: f.set_result(d),
        npt.CPROTO_RES_INSERT: lambda f, d: f.set_result(d),
        npt.CPROTO_RES_ACK: lambda f, d: f.set_result(None),
        npt.CPROTO_RES_AUTH_SUCCESS: lambda f, d: f.set_result(True),
        npt.CPROTO_RES_INFO: lambda f, d: f.set_result(d),
        npt.CPROTO_RES_FILE: lambda f, d: f.set_result(d),

        # SiriDB Client protocol error response types
        npt.CPROTO_ERR_MSG: lambda f, d: f.set_exception(
            RuntimeError(d.get('error_msg', None))),
        npt.CPROTO_ERR_QUERY: lambda f, d: f.set_exception(
            QueryError(d.get('error_msg', None))),
        npt.CPROTO_ERR_INSERT: lambda f, d: f.set_exception(
            InsertError(d.get('error_msg', None))),
        npt.CPROTO_ERR_SERVER: lambda f, d: f.set_exception(
            ServerError(d.get('error_msg', None))),
        npt.CPROTO_ERR_POOL: lambda f, d: f.set_exception(
            PoolError(d.get('error_msg', None))),
        npt.CPROTO_ERR_USER_ACCESS: lambda f, d: f.set_exception(
            UserAuthError(d.get('error_msg', None))),
        npt.CPROTO_ERR: lambda f, d: f.set_exception(
            RuntimeError(
                'Unexpected error occurred, view siridb log '
                'for more info')),
        npt.CPROTO_ERR_NOT_AUTHENTICATED: lambda f, d: f.set_exception(
            AuthenticationError('This connection is not authenticated')),
        npt.CPROTO_ERR_AUTH_CREDENTIALS: lambda f, d: f.set_exception(
            AuthenticationError('Invalid credentials')),
        npt.CPROTO_ERR_AUTH_UNKNOWN_DB: lambda f, d: f.set_exception(
            AuthenticationError('Unknown database')),
        npt.CPROTO_ERR_LOADING_DB: lambda f, d: f.set_exception(
            RuntimeError('Error loading database, '
                'please check the SiriDB log files')),
        npt.CPROTO_ERR_FILE: lambda f, d: f.set_exception(
            RuntimeError('Error retreiving file')),
    }

    def __init__(self, username, password, dbname):
        super().__init__()
        self._username = username
        self._password = password
        self._dbname = dbname
        self.auth_future = None

    def connection_made(self, transport):
        def finished(future):
            if not future.exception():
                self.on_authenticated()

        self._connected = True
        super().connection_made(transport)
        self.auth_future = self.send_package(npt.CPROTO_REQ_AUTH,
                                             data=(self._username,
                                                   self._password,
                                                   self._dbname),
                                             timeout=10)
        self.auth_future.add_done_callback(finished)
        self._password = None
        self.on_connection_made()

    def connection_lost(self, exc):
        self._connected = False
        super().connection_lost(exc)
        self.on_connection_lost()

    def on_package_received(self, pid, tipe, data=None, future=None):
        if future.cancelled():
            return
        self._MAP.get(tipe, lambda f, d: f.set_exception(
            TypeError('Client received an unknown package type: {}'
                      .format(tipe))))(future, data)

    def on_connection_made(self):
        pass

    def on_authenticated(self):
        pass

    def on_connection_lost(self):
        pass
