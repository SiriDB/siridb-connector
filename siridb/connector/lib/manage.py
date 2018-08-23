from .defaults import DEFAULT_CLIENT_PORT
from .defaults import DEFAULT_TIME_PRECISION
from .defaults import DEFAULT_BUFFER_SIZE
from .defaults import DEFAULT_DURATION_NUM
from .defaults import DEFAULT_DURATION_LOG


class SiriDBManage():

    def __init__(self, service_account, password):
        self._service_account = service_account
        self._password = password

    def connect(
            self,
            host='localhost',
            port=DEFAULT_CLIENT_PORT,
            loop=None,
            timeout=10):
        pass

    def info():
        pass

    def create_db(
            self,
            db_name,
            time_precision=DEFAULT_TIME_PRECISION,
            buffer_size=DEFAULT_BUFFER_SIZE,
            duration_num=DEFAULT_DURATION_NUM,
            duration_log=DEFAULT_DURATION_LOG):
        pass

    def create_pool(
            self, db_name, db_user, db_password, db_host, db_port=9000):
        pass

    def create_replica(
            self, pool, db_name, db_user, db_password, db_host, db_port=9000):
        pass

    def create_service_account(self, service_account, password):
        pass

    def drop_service_account(self, service_account):
        pass

    def change_password(self, new_password):
        pass


class AsyncSiriDBManage():

    async def connect():
        pass

    async def info():
        pass

    async def create_db():
        pass

    async def create_pool():
        pass

    async def create_replica():
        pass
