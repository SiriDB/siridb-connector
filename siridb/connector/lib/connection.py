


class SiriDBConnection():

    def __init__(self, loop):
        self._loop = loop or asyncio.get_event_loop()

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