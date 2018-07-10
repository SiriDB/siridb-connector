SiriDB - Connector
==================

The SiriDB Connector is a self-contained Python driver for communicating with SiriDB servers.
This manual describes how to install and configure SiriDB Connector for Python 3, and how to use it to develop database applications.


---------------------------------------
  * [Installation](#installation)
  * [Quick usage](#quick-usage)
  * [SiriDBClient](#siridbclient)
    * [connect](#siridbclientconnect)
    * [insert](#siridbclientinsert)
    * [query](#siridbclientquery)
    * [close](#siridbclientclose)
  * [Exception codes](#exception-codes)
  * [Version info](#version-info)

---------------------------------------

## Installation
------------

From PyPI (recommended)

```
pip install siridb-connector
```

From source code

```
python setup.py install
```


## Quick usage
-------

```python
import asyncio
import time
import random
from siridb.connector import SiriDBClient

async def example(siri):
    # Start connecting to SiriDB.
    # .connect() returns a list of all connections referring to the supplied
    # hostlist. The list can contain exceptions in case a connection could not
    # be made.
    await siri.connect()

    try:
        # insert
        ts = int(time.time())
        value = random.random()
        await siri.insert({'some_measurement': [[ts, value]]})

        # query
        resp = await siri.query('select * from "some_measurement"')
        print(resp)

    finally:
        # Close all SiriDB connections.
        siri.close()


siri = SiriDBClient(
    username='iris',
    password='siri',
    dbname='dbtest',
    hostlist=[('localhost', 9000)],  # Multiple connections are supported
    keepalive=True)

loop = asyncio.get_event_loop()
loop.run_until_complete(example(siri))
```


## SiriDBClient
Create a new SiriDB Client. This creates a new client but `.connect()` must be used to connect.

```python
siri = SiriDBClient(
    username=<username>,
    password=<password>,
    dbname=<dbname>,
    hostlist=[(<host>, <port>, {weight: 1}, {backup: False})],
    loop=None,
    keepalive=True,
    timeout=10,
    inactive_time=30,
    max_wait_retry=90)
```

Arguments:
* __username__: User with permissions to use the database.
* __password__: Password for the given username.
* __dbname__: Name of the database.
* __hostlist__: List with SiriDB servers (all servers or a subset of
servers can be in this list).


    *Example:*
    ```python
    hostlist=[ ('server1.local', 9000, {'weight': 3}),
               ('server2.local', 9001),
               ('backup1.local', 9002, {'backup': True}) ]
    ```
    Each server should at least have a hostname and port
    number. Optionally you can provide a dictionary with
    extra options.

    Available Options:
    - __weight__ : Should be a value between 1 and 9. A higher
                value gives the server more weight so it will
                be more likely chosen. (default 1)
    - __backup__ : Should be either True or False. When True the
                server will be marked as backup server and
                will only be chosen if no other server is
                available. (default: False)


Keyword arguments:
* __loop__: Asyncio loop. When 'None' the default event loop will be used.
* __keepalive__: When 'True' keep-alive packages are send every 45 seconds.
* __timeout__: Maximum time to complete a process, otherwise it will be cancelled.
* __inactive_time__: When a server is temporary unavailable, for
example the server could be paused, we mark the server as inactive after x seconds.
* __max_wait_retry__: When the reconnect loop starts, we try to reconnect in 1 second, then 2 seconds, 4, 8 and so on until max_wait_retry is reached and then use this value to retry again.
******************************************************************************

### SiriDBClient.connect

Start connecting to SiriDB. `.connect()` returns a list of all connections referring to the supplied hostlist. The list can contain exceptions in case a connection could not be made.

Optionally the keyword argument `timeout` can be set. This will constrain the search time for a connection. Exceeding the timeout will raise an `.TimeoutError`.

```python
siri.connect(timeout=None)
```

### SiriDBClient.insert

Insert time series data into SiriDB. Requires a 'dictionary' with at least one series.
Optionally the `timeout` can be adjusted (default: 300).

```python
siri.insert(data, timeout=300)
```

### SiriDBClient.query

Query data out of the database. Requires a string containing the query. More about the query language can be found [here](https://siridb.net/documentation/). The documentation about the query language will inform you about a number of useful aggregation and filter functions, different ways of visualizing and grouping the requested data, and how to make changes to the set up of the database. Optionally a `time_precision` (`SECOND`, `MICROSECOND`, `MILLISECOND`, `NANOSECOND`) can be set. The default `None` sets the precision to seconds. Futhermore the `timeout` can be adjusted (default: 60).

```python
from siridb.connector import (SECOND,
                              MICROSECOND,
                              MILLISECOND,
                              NANOSECOND)

siri.query(query, time_precision=None, timeout=60)
```

### SiriDBClient.close

Close the connection.

```python
siri.close()
```

Check if the connection is closed.

```python
siri.is_closed
```

## Exception codes

The following exceptions can be returned:

- `AuthenticationError`:
 *Raised when credentials are invalid or insufficient.*
- `IndexError`:
*Raised when the database does not exist (anymore).*
- `InsertError` (can only be raised when using the `.insert()` method):
 *Make sure the data is correct because this only happens when SiriDB could not process the request.*
- `OverflowError` (can only be raised when using the `.insert()` method):
 *Raised when integer values cannot not be packed due to an overflow error (integer values should be signed and not more than 63 bits).*
- `PoolError`:
 *SiriDB has no online server for at least one required pool. Try again later after some reasonable delay.*
- `QueryError` (can only be raised when using the `.query()` method):
 *Make sure the query is correct because this only happens when SiriDB could not process the query. Consult the [documentation](https://siridb.net/documentation/#help_select) about the query language can be found.*
- `RuntimeError`:
 *Raised when a general error message is received. This should no happen unless a new bug is discovered.*
- `ServerError`:
 *Raised when a server could not perform the request, you could try another server if one is available. Consult the [documentation](https://siridb.net/documentation/#help_list_servers) how to get additional status information about the servers.*
- `TimeoutError`:
 *Raised when a process lasts longer than the `timeout` period*
- `TypeError`:
 *Raised when an unknown package is received (might be caused by running a different SiriDB version).*
- `UserAuthError`:
 *The user as no rights to perform the insert or query. Consult the [documentation](https://siridb.net/documentation/#help_access) how to change the access rights.*

