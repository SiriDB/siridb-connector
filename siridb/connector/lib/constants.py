'''Constant values used by SiriDB.

:copyright: 2015, Jeroen van der Heijden (Transceptor Technology)
'''

import re
import logging

# this value is used when we shutdown SiriDB and when we pause a single server
# TIMEOUT_WAIT_FOR_TASKS = 120

# fifo buffer size used for buffering replica data
# FIFO_FILE_BUFFER_SIZE = 104857600  # 100MB

# max buffer size
# MAX_BUFFER_SIZE = 10485760  # 10MB (655295 points)

# series are dropped in batches with this size
# DROP_SERIES_PER_TASK = 8000

# shard version, will be saved to shard files which can be useful when we later
# want to migrate shards.
# SHARD_VERSION = 6

# series are evaluated in batches with this size
# EVAL_SERIES_PER_TASK = 250

# we auto connect when we see a server creating a connection so this is just
# in case that fails
# we do an attemps at the 1st hearbeat, at the second then the 4th, 8th
# and so on with a maximum of the value below.
# MAX_WAIT_RETRY_HEARTBEATS = 60

# this is the maximum sum for a series name in bytes. (8192 will accept at
# least 64 and approximately 80 characters)
# WARNING: DO NOT CHANGE THIS VALUE SINCE EXISTING POOLS WILL NOT BE
# ORDERED CORRECTLY
# MAX_SERIES_NAME_SUM = 8192

# both INSERT_TASKS and QUERY_TASKS share the same task counter but we can set
# different limits. (usually we should block queries first, then inserts)
# INSERT_TASKS_LIMIT = 130
# QUERY_TASKS_LIMIT = 90

# number of errors are accepted in a row. the counter will reset on a
# successful package but the connection will be closed when this number is
# reached.
# MAX_CONNECTION_ERROR_COUNT = 60

# time to wait before indexes are created.
# WAIT_BEFORE_CREATING_INDEXES = 10

# LIC_ROUNDS = 60213
# LIC_SECRET = 'DJjtqRqJS76L7tzkCBp6lg1LoZWQSuIEYlNkelERyNBdZI1GBxrhu2I'
# LIC_PREFIX = '$pbkdf2-sha256${}$'.format(LIC_ROUNDS)

# WARNING: Do not change these values since they are used by series index file
# _, _, _, _, _, _, INT64, _, _, DOUBLE, STRING = range(0, 11)

# status DB_OFFLINE will never be set to the own SiriDB status but only on
# 'other' server instances
# DB_OK = 0
# (DB_LOADING,
#     DB_SHUTTING_DOWN,
#     DB_LOCK_REINDEX,
#     DB_LOCK_REPLICATE,
#     DB_PAUSED,
#     DB_OFFLINE) = map(lambda x: 2 ** x, range(6))

# DB_MAP = {
#     DB_OK: 'running',
#     DB_LOADING: 'loading',
#     DB_SHUTTING_DOWN: 'shutting down',
#     DB_LOCK_REINDEX: 're-indexing',
#     DB_LOCK_REPLICATE: 'synchronizing',
#     DB_PAUSED: 'paused',
#     DB_OFFLINE: 'offline'
# }

# DO NOT CHANGE THESE! Shards are using them!
# (SHARD_SECONDS_BIT,
#  SHARD_MILLISECONDS_BIT,
#  SHARD_MICROSECONDS_BIT,
#  SHARD_NANOSECONDS_BIT) = range(4)

# VERY_LOW_PRIORITY = 1e-1
# LOW_PRIORITY = 1e-2
# MEDIUM_PRIORITY = 1e-3

# SHARD_OK = 0
# (SHARD_HAS_OVERLAP,
#     SHARD_MANUAL_OPTIMIZE,
#     SHARD_HAS_NEW_VALUES,
#     SHARD_HAS_REMOVED_SERIES,
#     SHARD_WILL_BE_REMOVED,
#     SHARD_WILL_BE_REPLACED) = map(lambda x: 2 ** x, range(6))

# (ACCESS_SELECT,
#     ACCESS_SHOW,
#     ACCESS_LIST,
#     ACCESS_CREATE,
#     ACCESS_INSERT,
#     ACCESS_DROP,
#     ACCESS_COUNT,
#     ACCESS_GRANT,
#     ACCESS_REVOKE,
#     ACCESS_ALTER,
#     ACCESS_PAUSE,
#     ACCESS_CONTINUE) = map(lambda x: 2 ** x, range(12))

# ACCESS_MAP = {
#     0: 'no access',
#     ACCESS_SELECT: 'select',
#     ACCESS_SHOW: 'show',
#     ACCESS_LIST: 'list',
#     ACCESS_CREATE: 'create',
#     ACCESS_INSERT: 'insert',
#     ACCESS_DROP: 'drop',
#     ACCESS_COUNT: 'count',
#     ACCESS_GRANT: 'grant',
#     ACCESS_REVOKE: 'revoke',
#     ACCESS_ALTER: 'alter',
#     ACCESS_PAUSE: 'pause',
#     ACCESS_CONTINUE: 'continue'
# }

# ACCESS_PROFILE_READ = ACCESS_SELECT | ACCESS_SHOW | ACCESS_LIST | ACCESS_COUNT
# ACCESS_PROFILE_WRITE = ACCESS_PROFILE_READ | ACCESS_CREATE | ACCESS_INSERT
# ACCESS_PROFILE_MODIFY = ACCESS_PROFILE_WRITE | ACCESS_DROP | ACCESS_ALTER
# ACCESS_PROFILE_FULL = \
#     ACCESS_PROFILE_MODIFY | ACCESS_GRANT | \
#     ACCESS_REVOKE | ACCESS_PAUSE | ACCESS_CONTINUE

# ACCESS_PROFILE_MAP = {
#     ACCESS_PROFILE_READ: 'read',
#     ACCESS_PROFILE_WRITE: 'write',
#     ACCESS_PROFILE_MODIFY: 'modify',
#     ACCESS_PROFILE_FULL: 'full'
# }


# Database name:
#    - minimum 2, maximum 20 chars
#    - starting with an alphabetic char
#    - middle can be hyphen or number or alphabetic chars
#    - ending with number or alphabetic char
DBNAME_VALID_NAME = re.compile('^[a-zA-Z][a-zA-Z0-9-_]{,18}[a-zA-Z0-9]$')

USER_MIN_LENGTH = 2
USER_MAX_LENGTH = 60
USER_DEFAULT = 'siri'

PASSWORD_MIN_LENGTH = 4
PASSWORD_MAX_LENGTH = 128
PASSWORD_DEFAULT = 'iris'

NETWORK_MAX_COMMENT_LENGTH = 255

TIMEOUT_MIN = 5.0
TIMEOUT_NORMAL = 30.0
TIMEOUT_LONG = 600.0
TIMEOUT_MAX = 1800.0

# Value between 0 and 1 to show how much (percent) we allow to drop at once.
# Note: currently we only use this on dropping series and will only be checked
#       on one pool. For example:
#    Say we have the drop_threshold set to 0.5 (50%) and we ask pool 0
#    to drop an amount of series. The threshold will only be check on this pool
#    so if pool 0 had a match of 40% and pool 1, 2 etc. have >50% we do not
#    receive a warning message.
DEFAULT_DROP_THRESHOLD = 1.0

DEFAULT_HTTP_PORT = 8090
DEFAULT_CLIENT_PORT = 9000
DEFAULT_BACKEND_PORT = 9010
DEFAULT_SESSION_COOKIE_MAX_AGE = 86400
DEFAULT_DB_PATH = '/var/lib/siridb/'
DEFAULT_OPTIMIZE_INTERVAL = 900
DEFAULT_HEARTBEAT_INTERVAL = 3
DEFAULT_CONFIG_FILE = '/etc/siridb/siridb.conf'
DEFAULT_MAX_CACHE_EXPRESSIONS = 10
DEFAULT_MAX_OPEN_FILES = 2000
DEFAULT_QUERY_TIMEOUT = 5
DEFAULT_TIMEZONE = 'NAIVE'
DEFAULT_LIST_LIMIT = 1000
DEFAULT_MAX_CHUNK_POINTS = 800
DEFAULT_BUFFER_SIZE = 1024

LOCAL_SERVER_PROPS = {
    'address',
    'name',
    'port',
    'uuid',
    'pool',
    'version',
    'online',
    'status'}

MAP_LOGLEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

PYTZ_VERSION = '2015.7'

SUCCESS_MSG = 'success_msg'
ERROR_MSG = 'error_msg'
