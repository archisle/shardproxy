shardproxy
==========

The module consists of two layers:

- ShardProxy class that just manages connections.
- ops module that implements helper classes for parallelism and result processing.

ShardProxy
----------

Initialize:

.. code:: python

    SHARD_URLS = [
        "postgresql+asyncpg://server/shard0",
        "postgresql+asyncpg://server/shard1",
    ]
    proxy = ShardProxy(SHARD_URLS)

Process request:

.. code:: python

    async def fetch_user(user_id: UUID):
        async with proxy.connect(user_id) as conn:
            async with conn.begin():
                stmt = select(User).where(User.id == user_id)
                res = await conn.execute(stmt)
                return res.all()

Operations
----------

Select bunch of IDs:

.. code:: python

    UserRow = Row[tuple[User]]

    class SelectManyUsers(RunOnKeysOperation[UserRow]):
        async def process(
            self, conn: AsyncConnection, keys: list[UUID]
        ) -> ResultRows[UserRow]:
            stmt = select(User).where(User.id.in_(keys))
            res = await conn.execute(stmt)
            return res.all()

    users = await SelectManyUsers().run(proxy)
