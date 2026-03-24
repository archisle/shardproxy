import asyncio
from typing import Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ColumnElement,
    ForeignKey,
    Row,
    String,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.functions import GenericFunction

from shardproxy import (
    AsyncConnection,
    ResultRows,
    RunOnAllOperation,
    RunOnArgsOperation,
    RunOnKeysOperation,
    RunOnOneOperation,
    ShardProxy,
)

SHARD_URLS = [
    "postgresql+asyncpg://localhost:5170/sharding1",
    "postgresql+asyncpg://localhost:5170/sharding2",
]

type DefaultRow[T] = Row[tuple[T]]


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    fullname: Mapped[Optional[str]]

    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"


class Address(Base):
    __tablename__ = "address"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))

    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"


class CreateUsers(RunOnArgsOperation[DefaultRow[User], User]):
    async def process(
        self, conn: AsyncConnection, args: dict[UUID, User]
    ) -> ResultRows[DefaultRow[User]]:
        stmt = (
            insert(User)
            .values(
                [dict(id=u.id, name=u.name, fullname=u.fullname) for u in args.values()]
            )
            .returning(User)
        )
        res = await conn.execute(stmt)

        addr_values = [
            dict(id=uuid4(), user_id=u.id, email_address=a.email_address)
            for u in args.values()
            for a in u.addresses
        ]
        if addr_values:
            stmt2 = insert(Address).values(addr_values)
            await conn.execute(stmt2)

        return res.all()


async def exec_create_users(proxy: ShardProxy) -> list[User]:
    spongebob = User(
        id=uuid4(),
        name="spongebob",
        fullname="Spongebob Squarepants",
        addresses=[Address(email_address="spongebob@sqlalchemy.org")],
    )
    sandy = User(
        id=uuid4(),
        name="sandy",
        fullname="Sandy Cheeks",
        addresses=[
            Address(email_address="sandy@sqlalchemy.org"),
            Address(email_address="sandy@squirrelpower.org"),
        ],
    )
    patrick = User(id=uuid4(), name="patrick", fullname="Patrick Star")
    args = {spongebob.id: spongebob, sandy.id: sandy, patrick.id: patrick}
    op = CreateUsers()
    await op.run(proxy, args)
    return [spongebob, sandy, patrick]


class SelectManyUsers(RunOnKeysOperation[DefaultRow[User]]):
    async def process(
        self, conn: AsyncConnection, keys: list[UUID]
    ) -> ResultRows[DefaultRow[User]]:
        stmt = select(User).where(User.id.in_(keys))
        res = await conn.execute(stmt)
        return res.all()


class SelectUsersWithManyAddresses(RunOnAllOperation[User]):
    async def process(
        self,
        conn: AsyncConnection,
    ) -> ResultRows[User]:
        result = await conn.execute(
            select(User, func.array_agg(Address.email_address).label("email_addresses"))
            .join(Address)
            .group_by(User.id)
            .having(func.count(Address.id) > 1)
        )
        res: list[User] = []
        for row in result.all():
            print(repr(row))
            res.append(
                User(
                    id=row.id,
                    name=row.name,
                    fullname=row.fullname,
                    addresses=[
                        Address(email_address=adr) for adr in row.email_addresses
                    ],
                )
            )
        return res


class UpdateOneUser(RunOnOneOperation[DefaultRow[User]]):
    def __init__(self, fullname: str):
        self.fullname = fullname

    async def process(
        self, conn: AsyncConnection, shard_key: UUID
    ) -> ResultRows[DefaultRow[User]]:
        stmt = (
            update(User)
            .values(fullname=self.fullname)
            .where(User.id == shard_key)
            .returning(User)
        )
        res = await conn.execute(stmt)
        return res.all()


class pg_sleep(GenericFunction[None]):
    """The CHAR_LENGTH() SQL function."""

    type = sqltypes.NULLTYPE
    inherit_cache = True

    def __init__(self, arg: ColumnElement[float], **kw: Any) -> None:
        super().__init__(arg, **kw)


class SyncSchema(RunOnAllOperation[dict[str, str]]):
    async def process(self, conn: AsyncConnection) -> ResultRows[dict[str, str]]:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        return []


async def main() -> None:
    proxy = ShardProxy(SHARD_URLS, echo=True)
    SELECT_MANY = SelectManyUsers()

    await SyncSchema().run(proxy)

    users = await exec_create_users(proxy)
    print("CreateUsers", users)

    ids = [u.id for u in users]
    usrs2 = await SELECT_MANY.run(proxy, ids)
    print("SelectManyUser", usrs2)

    usrs3 = await SelectUsersWithManyAddresses().run(proxy)
    print("SelectUsersWIthManyAddresses", usrs3)

    usrs4 = await UpdateOneUser("qwe").run(proxy, ids[0])
    print("UpdateOneUser", usrs4)


if __name__ == "__main__":
    asyncio.run(main())
