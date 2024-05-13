from pyeventor.plugins.postgres_store import PostgresAsyncEventStore, metadata
from pyeventor.asyncio.aggregate import AsyncAggregate
from pyeventor.event import Event
from pyeventor.decorator import register_handler
from datetime import datetime


class EventA(Event):
    ...


class EventB(Event):
    ...


class AggregateA(AsyncAggregate[int]):
    @register_handler(EventA)
    async def handle_event_a(self, event: EventA):
        print("Handling Event A")

    @register_handler(EventB)
    async def handle_event_b(self, event: EventB):
        print("Handling Event B")


class AggregateAStore(PostgresAsyncEventStore[datetime, str, AggregateA]):
    _AggregatedClass = AggregateA


store = AggregateAStore(
    database_url="postgresql+asyncpg://test_user:test_password@localhost:6666/test_db"
)


async def main():

    async with store.engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    a = AggregateA()

    b = EventB()

    await a.apply(b)

    await store.save(a)

    a = await store.load(a.id)


import asyncio

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

# @projection(AggregateB, [EventA, EventC])
# class ProjectionB(Projection):
#     @register_handler(EventC)
#     def handle_event_c(self, event: EventC):
#         print("Handling Event C in Projection B")
