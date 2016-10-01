'''Package Protocol.

Contains the PackageServerProtocol and PackageClientProtocol.
Both are subclasses from  _PackageProtocol.

:copyright: 2015, Jeroen van der Heijden (Transceptor Technology)
'''

import asyncio
import logging
import msgpack
from . import qpack
from .datapackage import DataPackage
from . import networkpackets as npt

_MAP = (
    lambda data: b'',
    lambda data: qpack_safe(data),
    lambda data: data
)

#
# 2 MB is the maximum package size which is allowed by SiriDB
# but even lower size packages are recommended. (< 1 MB)
#
MAX_PACKAGE_SZ = 2000000


def qpack_safe(data):
    packed = qpack.packb(data)
    size = len(packed)
    if size > MAX_PACKAGE_SZ:
        raise ValueError(
            'Package size too large (got {} bytes, max allowed: {} bytes)'
            .format(size, MAX_PACKAGE_SZ))
    return packed


def pack(tipe, data=None):
    assert tipe in npt.MAP_REQ_DTYPE, \
        'No data type found for message type: {}'.format(tipe)
    return _MAP[npt.MAP_REQ_DTYPE[tipe]](data)


class _PackageProtocol(asyncio.Protocol):

    def __init__(self):
        self._buffered_data = bytearray()
        self._data_package = None

    def connection_made(self, transport):
        '''
        override asyncio.Protocol
        '''
        self.transport = transport
        self.remote_ip, self.port = transport.get_extra_info('peername')[:2]
        logging.info(
            'Connection made (address: {} port: {})'
            .format(self.remote_ip, self.port))

    def connection_lost(self, exc):
        '''
        override asyncio.Protocol
        '''
        logging.info(
            'Connection lost (address: {} port: {})'
            .format(self.remote_ip, self.port))

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

    def send_package(self, pid, tipe, data=None, is_binary=False):
        if not is_binary:
            data = pack(tipe, data)
        header = DataPackage.struct_datapackage.pack(len(data), pid, tipe, tipe ^ 255)
        self.transport.write(header + data)

    def _on_package_received(self):
        self.on_package_received(
            self._data_package.pid,
            self._data_package.tipe,
            self._data_package.data
        )

    def on_package_received(self, pid, tipe, data=None, future=None):
        '''
        Implement this method for handling received package.
        (The future is used only for the PackageClientProtocol and will
        be None otherwise)'''
        pass


class PackageClientProtocol(_PackageProtocol):

    def __init__(self):
        super().__init__()
        self._pid = 0
        self._requests = {}

    def connection_lost(self, exc):
        super().connection_lost(exc)
        for pid, (future, task) in self._requests.items():
            task.cancel()
            if future.cancelled():
                continue
            future.set_exception(ConnectionError(
                'Connection is lost before we had an answer on package id: {}.'
                .format(pid)))

    async def _timeout_request(self, pid, timeout, tipe):
        await asyncio.sleep(timeout)
        if not self._requests[pid][0].cancelled():
            self._requests[pid][0].set_exception(TimeoutError(
                'Request timed out on PID {} ({})'
                .format(pid, npt.TEXT_REQ_MAP.get(tipe, 'UNKNOWN'))))
        del self._requests[pid]

    def send_package(self, tipe, data=None, is_binary=False, timeout=3600):
        self._pid += 1
        self._pid %= 65536
        super().send_package(self._pid, tipe, data=data, is_binary=is_binary)
        task = asyncio.ensure_future(self._timeout_request(self._pid,
                                                           timeout,
                                                           tipe))
        future = asyncio.Future()
        self._requests[self._pid] = (future, task)
        return future

    def _on_package_received(self):
        try:
            future, task = self._requests.pop(self._data_package.pid)
        except KeyError:
            logging.error(
                'Package ID not found: {} ({})'.format(
                    self._data_package.pid,
                    npt.TEXT_RES_MAP.get(self._data_package.tipe, 'UNKNOWN')))
            return None

        # cancel the timeout task
        task.cancel()

        self.on_package_received(
            self._data_package.pid,
            self._data_package.tipe,
            self._data_package.data,
            future)
