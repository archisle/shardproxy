"""Connection manager for sharding."""

from collections.abc import Mapping, Sequence
from random import choice
from typing import Unpack
from uuid import UUID

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)

from .types import AsyncEngineParams

__all__ = ("ShardProxy",)


class ShardProxy:
    """Manages AsyncEngine mapping for shards.

    Takes list of shard URLs and generic create_async_engine()/create_engine()
    keyword arguments.
    """

    _shards: list[AsyncEngine]

    def __init__(
        self, shard_urls: Sequence[str | URL], **kwargs: Unpack[AsyncEngineParams]
    ) -> None:
        self._shards = []
        for url in shard_urls:
            engine = create_async_engine(url, **kwargs)
            self._shards.append(engine)

    def _get_shard(self, shard_key: UUID) -> int:
        return shard_key.node % len(self._shards)

    @property
    def shards(self) -> Sequence[AsyncEngine]:
        """Read-only list of engines per shard.

        Usage::

            # run-on-all: serial mode
            for engine in proxy.shards:
                async with engine.connect() as conn:
                    async with conn.begin():
                        await conn.execute()

            # run-on-all: parallel mode
            async with asyncio.TaskGroup() as tg:
                for engine in proxy.shards:
                    tg.create_task(process(engine, items))
        """
        return self._shards

    def connect(self, shard_key: UUID) -> AsyncConnection:
        """Returns connection for specific shard as context manager.

        Usage::

            async with proxy.connect(key) as conn:
                async with conn.begin():
                    ...
        """
        idx = self._get_shard(shard_key)
        return self._shards[idx].connect()

    def connect_any[T](self) -> AsyncConnection:
        """Returns connection to random shard as context manager.

        Usage::

            async with proxy.connect_any() as conn:
                async with conn.begin():
                    ...
        """
        engine = choice(self._shards)
        return engine.connect()

    def spread_args[A](
        self, args: Mapping[UUID, A]
    ) -> Sequence[tuple[AsyncEngine, dict[UUID, A]]]:
        """Spread keys with arguments over shards.

        Usage::

            # serial mode
            for engine, shard_items in proxy.split_args(all_items):
                async with engine.connect() as conn:
                    async with conn.begin():
                        await conn.execute()

            # parallel mode
            async with asyncio.TaskGroup() as tg:
                for engine, items in proxy.split_args(all_items):
                    tg.create_task(process(engine, items))
        """
        split: dict[int, dict[UUID, A]] = {}
        for key, arg in args.items():
            nr = self._get_shard(key)
            target = split.get(nr)
            if target is None:
                split[nr] = {key: arg}
            else:
                target[key] = arg
        return [(self._shards[nr], target) for nr, target in split.items()]

    def spread_keys(
        self, keys: Sequence[UUID]
    ) -> Sequence[tuple[AsyncEngine, list[UUID]]]:
        """Spread keys over shards.

        Usage::

            # serial mode
            for engine, shard_keys in proxy.split_keys(all_keys):
                async with engine.connect() as conn:
                    async with conn.begin():
                        await conn.execute()

            # parallel mode
            async with asyncio.TaskGroup() as tg:
                for engine, shard_keys in proxy.split_keys(all_keys):
                    tg.create_task(process(engine, shard_keys))
        """
        split: dict[int, set[UUID]] = {}
        for key in keys:
            nr = self._get_shard(key)
            target = split.get(nr)
            if target is None:
                target = split[nr] = set()
            target.add(key)
        return [(self._shards[nr], list(target)) for nr, target in split.items()]
