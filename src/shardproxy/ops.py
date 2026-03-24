"""Helper classes for multi-shard operations."""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from .proxy import ShardProxy
from .types import DBTask, ResultRows

__all__ = (
    "RunOnKeysOperation",
    "RunOnArgsOperation",
    "RunOnAllOperation",
    "RunOnOneOperation",
    "RunOnAnyOperation",
)


class RunOnKeysOperation[TRow](ABC):
    """Runs operation over given keys.

    Usage::

        class MyOp(RunOnKeysOperation[MyRow]):
            async def process(
                self, conn: AsyncConnection, keys: list[UUID]
            ) -> ResultRows[MyRow]:
                return ...

    """

    #: Whether connection is in transaction context when given to .process().
    USE_TRANSACTION = True

    @abstractmethod
    async def process(
        self, conn: AsyncConnection, keys: list[UUID]
    ) -> ResultRows[TRow]:
        """Business logic to execute on each shard."""
        raise NotImplementedError

    async def run(
        self, proxy: ShardProxy, shard_keys: Sequence[UUID]
    ) -> ResultRows[TRow]:
        """Split keys for each shard and run .process() on them."""

        tasks: list[DBTask[ResultRows[TRow]]] = []
        for engine, keys in proxy.spread_keys(shard_keys):
            task = asyncio.create_task(self._handle_process(engine, keys))
            tasks.append(task)

        return await self._collect(tasks)

    async def _handle_process(
        self, engine: AsyncEngine, keys: list[UUID]
    ) -> ResultRows[TRow]:
        async with engine.connect() as conn:
            if self.USE_TRANSACTION:
                async with conn.begin():
                    return await self.process(conn, keys)
            else:
                return await self.process(conn, keys)

    async def _collect(self, tasks: list[DBTask[ResultRows[TRow]]]) -> ResultRows[TRow]:
        shard_rows = await asyncio.gather(*tasks)
        res: list[TRow] = []
        for rows in shard_rows:
            res.extend(rows)
        return res


class RunOnArgsOperation[TRow, TArg](ABC):
    """Runs operation over given arguments.

    Usage::

        class MyOp(RunOnArgsOperation[MyRow, MyArg]):
            async def process(
                self, conn: AsyncConnection, args: dict[UUID, MyArg]
            ) -> ResultRows[MyRow]:
                return ...

    """

    #: Whether connection is in transaction context when given to .process().
    USE_TRANSACTION = True

    @abstractmethod
    async def process(
        self, conn: AsyncConnection, args: dict[UUID, TArg]
    ) -> ResultRows[TRow]:
        """Business logic to execute on each shard."""
        raise NotImplementedError

    async def run(self, proxy: ShardProxy, args: dict[UUID, TArg]) -> ResultRows[TRow]:
        """Split args for each shard and run .process() with them."""

        tasks: list[DBTask[ResultRows[TRow]]] = []
        for engine, shard_args in proxy.spread_args(args):
            task = asyncio.create_task(self._handle_process(engine, shard_args))
            tasks.append(task)

        return await self._collect(tasks)

    async def _handle_process(
        self, engine: AsyncEngine, args: dict[UUID, TArg]
    ) -> ResultRows[TRow]:
        async with engine.connect() as conn:
            if self.USE_TRANSACTION:
                async with conn.begin():
                    return await self.process(conn, args)
            else:
                return await self.process(conn, args)

    async def _collect(self, tasks: list[DBTask[ResultRows[TRow]]]) -> ResultRows[TRow]:
        shard_rows = await asyncio.gather(*tasks)
        res: list[TRow] = []
        for rows in shard_rows:
            res.extend(rows)
        return res


class RunOnAllOperation[TRow](ABC):
    """Runs operation over all shards.

    Usage::

        class MyOp(RunOnAllOperation[MyRow]):
            async def process(
                self, conn: AsyncConnection
            ) -> ResultRows[MyRow]:
                return ...

    """

    #: Whether connection is in transaction context when given to .process().
    USE_TRANSACTION = True

    @abstractmethod
    async def process(self, conn: AsyncConnection) -> ResultRows[TRow]:
        """Business logic to execute on each shard."""
        raise NotImplementedError

    async def run(self, proxy: ShardProxy) -> ResultRows[TRow]:
        """Loop over all shards, execute .process() on each."""

        tasks: list[DBTask[ResultRows[TRow]]] = []
        for engine in proxy.shards:
            task = asyncio.create_task(self._handle_process(engine))
            tasks.append(task)

        return await self._collect(tasks)

    async def _handle_process(self, engine: AsyncEngine) -> ResultRows[TRow]:
        async with engine.connect() as conn:
            if self.USE_TRANSACTION:
                async with conn.begin():
                    return await self.process(conn)
            else:
                return await self.process(conn)

    async def _collect(self, tasks: list[DBTask[ResultRows[TRow]]]) -> ResultRows[TRow]:
        shard_rows = await asyncio.gather(*tasks)
        res: list[TRow] = []
        for rows in shard_rows:
            res.extend(rows)
        return res


class RunOnOneOperation[TRow](ABC):
    """Runs operation in single shard.

    Usage::

        class MyOp(RunOnOneOperation[MyRow]):
            async def process(
                self, conn: AsyncConnection, shard_key: UUID
            ) -> ResultRows[MyRow]:
                return ...

    """

    #: Whether connection is in transaction context when given to .process().
    USE_TRANSACTION = True

    @abstractmethod
    async def process(self, conn: AsyncConnection, shard_key: UUID) -> ResultRows[TRow]:
        """Business logic to execute on shard."""
        raise NotImplementedError

    async def run(self, proxy: ShardProxy, shard_key: UUID) -> ResultRows[TRow]:
        """Pick shard and run .process() on it."""

        async with proxy.connect(shard_key) as conn:
            if self.USE_TRANSACTION:
                async with conn.begin():
                    return await self.process(conn, shard_key)
            else:
                return await self.process(conn, shard_key)


class RunOnAnyOperation[TRow](ABC):
    """Runs operation in single random shard.

    Usage::

        class MyOp(RunOnAnyOperation[MyRow]):
            async def process(
                self, conn: AsyncConnection
            ) -> ResultRows[MyRow]:
                return ...

    """

    #: Whether connection is in transaction context when given to .process().
    USE_TRANSACTION = True

    @abstractmethod
    async def process(self, conn: AsyncConnection) -> ResultRows[TRow]:
        """Business logic to execute on shard."""
        raise NotImplementedError

    async def run(self, proxy: ShardProxy) -> ResultRows[TRow]:
        """Pick random shard and run .process() on it."""

        async with proxy.connect_any() as conn:
            if self.USE_TRANSACTION:
                async with conn.begin():
                    return await self.process(conn)
            else:
                return await self.process(conn)
