"""Common types"""

import asyncio
from collections.abc import Sequence
from typing import Any, Callable, Literal, Type, TypedDict

from sqlalchemy.engine.interfaces import (
    CoreExecuteOptionsParameter,
    IsolationLevel,
)
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.pool import Pool

__all__ = (
    "AsyncConnection",
    "AsyncEngine",
    "AsyncEngineParams",
    "ResultRows",
    "DBTask",
)


type ResultRows[TRow] = Sequence[TRow]

type DBTask[TResult] = asyncio.Task[TResult]


class AsyncEngineParams(TypedDict, total=False):
    """Helper struct to describe common parameters for create_async_engine.

    It may be incomplete - arguments from here are
    passed to AsyncEngine, Dialect and Pool.

    Some values are deliberately hidden as they will not work with ShardProxy.
    """

    # async_creator - does not work with sharding
    # connect_args - does not work with sharding
    echo: bool | Literal["debug"] | None
    echo_pool: bool | Literal["debug"] | None
    enable_from_linting: bool
    execution_options: CoreExecuteOptionsParameter
    hide_parameters: bool
    insertmanyvalues_page_size: int
    isolation_level: IsolationLevel
    json_deserializer: Callable[..., Any]
    json_serializer: Callable[..., Any]
    label_length: int | None
    logging_name: str
    max_identifier_length: int
    max_overflow: int
    # module - does not work with sharding
    paramstyle: Literal[
        "qmark", "numeric", "named", "format", "pyformat", "numeric_dollar"
    ]
    # pool - does not work with sharding
    poolclass: Type[Pool]
    pool_logging_name: str
    pool_pre_ping: bool
    pool_size: int
    pool_recycle: int
    pool_reset_on_return: Literal["rollback", "commit"] | None
    pool_timeout: int
    pool_use_iifo: bool
    plugins: list[str]
    query_cache_size: int
    skip_autocommit_rollback: bool
    use_insertmanyvalues: bool
