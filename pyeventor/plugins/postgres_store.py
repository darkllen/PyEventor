from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    ForeignKey,
    Table,
    MetaData,
)
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from pyeventor.asyncio.event_store import (
    AsyncEventStore,
    IdTypeHint,
    Snapshot,
    SequenceHint,
    AggregateAsyncHint,
)
from pyeventor.event import Event
from typing import Type, Optional, List
from pyeventor.handler import EventHandler


metadata = MetaData()

event_table = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("aggregate_id", String, nullable=False),
    Column("type", String, nullable=False),
    Column("data", JSON),
    Column("sequence_order", DateTime, default=datetime.utcnow),
)

snapshot_table = Table(
    "snapshots",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("aggregate_id", String, nullable=False),
    Column("type", String, nullable=False),
    Column("data", JSON),
    Column("sequence_order", DateTime, default=datetime.utcnow),
)


class PostgresAsyncEventStore(
    AsyncEventStore[SequenceHint, IdTypeHint, AggregateAsyncHint]
):
    def __init__(self, database_url):
        self.engine = create_async_engine(database_url)
        self.async_session_factory = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    @asynccontextmanager
    async def transaction(self):
        """Provide a transactional scope around a series of operations."""
        async with self.async_session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception as e:
                    await session.rollback()  # Rollback transaction on errors
                    raise e
                else:
                    await session.commit()  # Explicit commit if no errors

    async def save_events(self, events: List[Event], aggregate_id: IdTypeHint) -> None:
        async with self.transaction() as session:
            for event in events:
                await session.execute(
                    event_table.insert().values(
                        aggregate_id=aggregate_id,
                        type=event.__class__.__name__,
                        data=event.data,
                        sequence_order=event.sequence_order,
                    )
                )

    async def save_snapshots(
        self, snapshots: list[Snapshot], aggregate_id: IdTypeHint
    ) -> None:
        async with self.transaction() as session:
            for snapshot in snapshots:
                await session.execute(
                    snapshot_table.insert().values(
                        aggregate_id=aggregate_id,
                        type=snapshot.__class__.__name__,
                        data=snapshot.data,
                        sequence_order=snapshot.sequence_order,
                    )
                )

    async def get_events(
        self,
        aggregate_id: IdTypeHint,
        event_types: list[Type[Event]] = [],
        gt: Optional[SequenceHint] = None,
        lte: Optional[SequenceHint] = None,
    ) -> List[Event]:
        async with self.async_session_factory() as session:
            stmt = select(event_table).where(event_table.c.aggregate_id == aggregate_id)
            if event_types:
                stmt = stmt.where(
                    event_table.c.type.in_([et.__name__ for et in event_types])
                )
            if gt:
                stmt = stmt.where(event_table.c.sequence_order > gt)
            if lte:
                stmt = stmt.where(event_table.c.sequence_order <= lte)
            result = await session.execute(stmt)

            events = []
            for r in result.all():
                event_class = EventHandler.get_event_class_by_name(r[2])
                event = event_class(data=r[3], sequence_order=r[4])
                events.append(event)

            return events

    async def get_last_snapshot(
        self,
        aggregate_id: IdTypeHint,
        snapshot_type: Optional[Type[Snapshot]] = None,
        load_at: Optional[SequenceHint] = None,
    ) -> Optional[Snapshot]:
        async with self.async_session_factory() as session:
            stmt = select(snapshot_table).where(
                snapshot_table.c.aggregate_id == aggregate_id
            )
            if snapshot_type:
                stmt = stmt.where(snapshot_table.c.type == snapshot_type.__name__)
            if load_at:
                stmt = stmt.where(snapshot_table.c.sequence_order <= load_at)
            stmt = stmt.order_by(snapshot_table.c.sequence_order.desc())
            result = await session.execute(stmt)
            raw = result.first()
            if raw:
                snapshot_class = self._AggregatedClass.SnapshotClass
                snapshot = snapshot_class(data=raw[3], sequence_order=raw[4])

                return snapshot
