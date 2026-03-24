from uuid import UUID

import pytest
from sqlalchemy import Row, literal, select

from shardproxy import (
    AsyncConnection,
    ResultRows,
    RunOnAllOperation,
    RunOnArgsOperation,
    RunOnKeysOperation,
)
from shardproxy.ops import RunOnAnyOperation, RunOnOneOperation

from helpers import DRIVERS, get_proxy, pg_sleep

U0 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77bea0")
U1 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77beb1")
U2 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77bec2")
U3 = UUID("ab406ecc-fa65-4d13-aef6-2d684d77bed3")

type TestRow = Row[tuple[int]]


async def run_statement(conn: AsyncConnection, desc: str) -> ResultRows[TestRow]:
    stmt0 = select(pg_sleep(literal(0.05)).label(desc))
    await conn.execute(stmt0)
    stmt = select(literal(1).label("value"))
    res = await conn.execute(stmt)
    return res.all()


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_all(driver: str) -> None:
    proxy = get_proxy(driver)

    class Demo(RunOnAllOperation[TestRow]):
        async def process(self, conn: AsyncConnection) -> ResultRows[TestRow]:
            return await run_statement(conn, "RunOnAllOperation")

    op = Demo()
    res = await op.run(proxy)
    assert len(res) == len(proxy.shards)


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_keys(driver: str) -> None:
    proxy = get_proxy(driver)

    class Demo(RunOnKeysOperation[TestRow]):
        async def process(
            self, conn: AsyncConnection, keys: list[UUID]
        ) -> ResultRows[TestRow]:
            return await run_statement(conn, "RunOnKeysOperation")

    op = Demo()
    res = await op.run(proxy, [U0, U1, U2, U3])
    assert len(res) == len(proxy.shards)


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_args(driver: str) -> None:
    proxy = get_proxy(driver)

    class Demo(RunOnArgsOperation[TestRow, str]):
        async def process(
            self, conn: AsyncConnection, args: dict[UUID, str]
        ) -> ResultRows[TestRow]:
            return await run_statement(conn, "RunOnArgsOperation")

    op = Demo()
    res = await op.run(proxy, {U0: "a", U1: "b", U2: "c", U3: "d"})
    assert len(res) == len(proxy.shards)


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_any(driver: str) -> None:
    proxy = get_proxy(driver)

    class Demo(RunOnAnyOperation[TestRow]):
        async def process(self, conn: AsyncConnection) -> ResultRows[TestRow]:
            return await run_statement(conn, "RunOnAnyOperation")

    op = Demo()
    res = await op.run(proxy)
    assert len(res) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("driver", DRIVERS)
async def test_run_on_one(driver: str) -> None:
    proxy = get_proxy(driver)

    class Demo(RunOnOneOperation[TestRow]):
        async def process(
            self, conn: AsyncConnection, shard_key: UUID
        ) -> ResultRows[TestRow]:
            return await run_statement(conn, "RunOnOneOperation")

    op = Demo()
    res = await op.run(proxy, U0)
    assert len(res) == 1
