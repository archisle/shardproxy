from typing import Any

from sqlalchemy import ColumnElement
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.functions import GenericFunction

from shardproxy import ShardProxy

DRIVER_URLS = {
    "asyncpg": [
        "postgresql+asyncpg://localhost:5170/sharding1",
        "postgresql+asyncpg://localhost:5170/sharding2",
    ],
    "psycopg": [
        "postgresql+psycopg://localhost:5170/sharding1",
        "postgresql+psycopg://localhost:5170/sharding2",
    ],
}

DRIVERS = tuple(DRIVER_URLS.keys())


def get_proxy(driver: str) -> ShardProxy:
    urls = DRIVER_URLS[driver]
    return ShardProxy(urls)


class pg_sleep(GenericFunction[None]):
    """Sleep in database."""

    type = sqltypes.NULLTYPE
    inherit_cache = True

    def __init__(self, arg: ColumnElement[float], **kw: Any) -> None:
        super().__init__(arg, **kw)
