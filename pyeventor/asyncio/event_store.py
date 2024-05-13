from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Type, Protocol
from pyeventor.event import Event, Snapshot
from pyeventor.aggregate import Aggregate, Projection, IdTypeHint
from pyeventor.asyncio.aggregate import AsyncAggregate
from pyeventor.handler import EventHandler
from contextlib import asynccontextmanager

AggregateAsyncHint = TypeVar("AggregateAsyncHint", bound=AsyncAggregate)
SequenceHint = TypeVar("SequenceHint")


class SnapshotStoreAsyncI(Protocol, Generic[IdTypeHint, SequenceHint]):
    @abstractmethod
    async def save_snapshots(
        self, snapshots: list[Snapshot], aggregate_id: IdTypeHint
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get_last_snapshot(
        self,
        aggregate_id: IdTypeHint,
        snapshot_type: Optional[Type[Snapshot]] = None,
        load_at: Optional[SequenceHint] = None,
    ) -> Optional[Snapshot]:
        """
        Retrieve all events associated with a given aggregate ID.
        This can be useful for historical queries or debugging purposes.
        """
        raise NotImplementedError()


class EventStoreAsyncI(Protocol, Generic[SequenceHint, IdTypeHint, AggregateAsyncHint]):
    _AggregatedClass: Type[AggregateAsyncHint]

    @abstractmethod
    async def get_events(
        self,
        aggregate_id: IdTypeHint,
        event_types: list[Type[Event]] = [],
        gt: Optional[SequenceHint] = None,
        lte: Optional[SequenceHint] = None,
    ) -> List[Event]:
        """
        Retrieve all events associated with a given aggregate ID.
        This can be useful for historical queries or debugging purposes.
        """
        raise NotImplementedError()

    @abstractmethod
    async def save_events(self, events: List[Event], aggregate_id: IdTypeHint) -> None:
        """
        Retrieve all events associated with a given aggregate ID.
        This can be useful for historical queries or debugging purposes.
        """
        raise NotImplementedError()

    @asynccontextmanager
    async def transaction(self):
        yield

    @abstractmethod
    async def save(self, aggregate: AggregateAsyncHint) -> None:
        ...

    @abstractmethod
    async def load(
        self,
        aggregate_id: IdTypeHint,
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[AggregateAsyncHint]:
        ...


class ProjectionStoreAsyncI(Protocol, Generic[SequenceHint]):
    @abstractmethod
    async def load_projection(
        self,
        aggregate_id: IdTypeHint,
        projection_class: Type[Projection],
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[Projection]:
        ...


class AsyncEventStore(
    ABC,
    EventStoreAsyncI[SequenceHint, IdTypeHint, AggregateAsyncHint],
    ProjectionStoreAsyncI[SequenceHint],
    SnapshotStoreAsyncI[IdTypeHint, SequenceHint],
):
    async def save(self, aggregate: AggregateAsyncHint) -> None:
        async with self.transaction():
            events_for_save = aggregate.uncommmited_events
            if not events_for_save:
                return

            snapshots = [s for s in events_for_save if isinstance(s, Snapshot)]
            events_without_snapshots = [
                s for s in events_for_save if not isinstance(s, Snapshot)
            ]
            if snapshots:
                await self.save_snapshots(snapshots, aggregate.id)
            if events_without_snapshots:
                await self.save_events(events_without_snapshots, aggregate.id)
            aggregate.uncommmited_events.clear()

    async def load(
        self,
        aggregate_id: IdTypeHint,
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[AggregateAsyncHint]:

        snapshot = (
            await self.get_last_snapshot(
                aggregate_id,
                snapshot_type=self._AggregatedClass.SnapshotClass,
                load_at=load_at,
            )
            if from_snapshots
            else None
        )
        if snapshot:
            actual_snapshot = snapshot.upcast()
            while type(actual_snapshot) != type(snapshot):
                snapshot = actual_snapshot
                actual_snapshot = snapshot.upcast()

            aggregate = self._AggregatedClass.from_snapshot(aggregate_id, snapshot)
            all_events = await self.get_events(
                aggregate_id, lte=load_at, gt=snapshot.sequence_order
            )
        else:
            all_events = await self.get_events(aggregate_id, lte=load_at)
            aggregate = self._AggregatedClass(aggregate_id)

            for event in all_events:
                actual_event = event.upcast()
                while not isinstance(actual_event, type(event)):
                    event = actual_event
                    actual_event = event.upcast()
                await aggregate._apply_without_saving(actual_event)

        return aggregate

    async def load_projection(
        self,
        aggregate_id: IdTypeHint,
        projection_class: Type[Projection],
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[Projection]:

        projection_events = list(
            EventHandler.get_aggregate_handlers(projection_class).keys()
        )

        snapshot = (
            await self.get_last_snapshot(
                aggregate_id,
                snapshot_type=projection_class.SnapshotClass,
                load_at=load_at,
            )
            if from_snapshots
            else None
        )
        if snapshot:
            actual_snapshot = snapshot.upcast()
            while type(actual_snapshot) != type(snapshot):
                snapshot = actual_snapshot
                actual_snapshot = snapshot.upcast()

            aggregate = projection_class.from_snapshot(aggregate_id, snapshot)
            all_events = await self.get_events(
                aggregate_id, projection_events, lte=load_at, gt=snapshot.sequence_order
            )
        else:
            all_events = await self.get_events(
                aggregate_id, projection_events, lte=load_at
            )
            aggregate = projection_class(aggregate_id)

        for event in all_events:
            actual_event = event.upcast()
            while not isinstance(actual_event, type(event)):
                event = actual_event
                actual_event = event.upcast()
            await aggregate.apply(actual_event)

        return aggregate
