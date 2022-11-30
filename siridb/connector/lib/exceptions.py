'''Custom exceptions used by SiriDB.

:copyright: 2022, Jeroen van der Heijden (Cesbit.com)
'''


class QueryError(Exception):
    pass


class InsertError(Exception):
    pass


class ServerError(Exception):
    pass


class PoolError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class UserAuthError(AuthenticationError):
    pass
