import asyncio
from uuid import UUID

import pytest
from sqlalchemy import literal, select

from shardproxy import AsyncConnection, AsyncEngine

from helpers import DRIVERS, get_proxy, pg_sleep

U0 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77bea0")
U1 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77beb1")
U2 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77bec2")
U3 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77bed3")


async def run_statement(conn: AsyncConnection, desc: str) -> None:
    stmt = select(pg_sleep(literal(0.05)).label(desc))
    await conn.execute(stmt)


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_all_seq(driver: str) -> None:
    proxy = get_proxy(driver)
    nr = 0
    for engine in proxy.shards:
        async with engine.connect() as conn:
            async with conn.begin():
                await run_statement(conn, "run-on-all-seq")
                nr += 1
    assert nr == len(proxy.shards)


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_all_parallel(driver: str) -> None:
    proxy = get_proxy(driver)
    nr = 0

    async def runner(engine: AsyncEngine) -> None:
        nonlocal nr
        async with engine.connect() as conn:
            async with conn.begin():
                await run_statement(conn, "run-on-all-parallel")
        nr += 1

    async with asyncio.TaskGroup() as tg:
        for engine in proxy.shards:
            tg.create_task(runner(engine))

    assert nr == len(proxy.shards)


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_connect(driver: str) -> None:
    proxy = get_proxy(driver)
    async with proxy.connect(U0) as conn:
        async with conn.begin():
            await run_statement(conn, "connect")


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_connect_any(driver: str) -> None:
    proxy = get_proxy(driver)
    async with proxy.connect_any() as conn:
        async with conn.begin():
            await run_statement(conn, "connect-any")


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_spread_keys_seq(driver: str) -> None:
    proxy = get_proxy(driver)
    nr = 0
    for engine, keys in proxy.spread_keys([U0, U1, U2, U3]):
        assert len(keys) == 2
        async with engine.connect() as conn:
            async with conn.begin():
                await run_statement(conn, "spread-keys-seq")
                nr += 1
    assert nr == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_spread_keys_parallel(driver: str) -> None:
    proxy = get_proxy(driver)
    all_keys = [U0, U1, U2, U3]
    nr = 0

    async def runner(engine: AsyncEngine, args: list[UUID]) -> None:
        nonlocal nr
        async with engine.connect() as conn:
            async with conn.begin():
                await run_statement(conn, "spread-keys-parallel")
        nr += 1

    async with asyncio.TaskGroup() as tg:
        for engine, keys in proxy.spread_keys(all_keys):
            assert len(keys) == 2
            tg.create_task(runner(engine, keys))

    assert nr == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_spread_args_seq(driver: str) -> None:
    proxy = get_proxy(driver)
    all_args = {U0: "U0", U1: "U1", U2: "U2", U3: "U3"}
    nr = 0
    for engine, args in proxy.spread_args(all_args):
        assert len(args) == 2
        async with engine.connect() as conn:
            async with conn.begin():
                await run_statement(conn, "spread-args-seq")
                nr += 1
    assert nr == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_spread_args_parallel(driver: str) -> None:
    proxy = get_proxy(driver)
    all_args = {U0: "U0", U1: "U1", U2: "U2", U3: "U3"}
    nr = 0

    async def runner(engine: AsyncEngine, args: dict[UUID, str]) -> None:
        nonlocal nr
        async with engine.connect() as conn:
            async with conn.begin():
                await run_statement(conn, "spread-args-parallel")
        nr += 1

    async with asyncio.TaskGroup() as tg:
        for engine, args in proxy.spread_args(all_args):
            assert len(args) == 2
            tg.create_task(runner(engine, args))

    assert nr == 2
