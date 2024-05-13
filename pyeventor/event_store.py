from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Type, Protocol
from pyeventor.event import Event, Snapshot
from pyeventor.aggregate import Aggregate, Projection, IdTypeHint
from pyeventor.handler import EventHandler
from contextlib import contextmanager

AggregateHint = TypeVar("AggregateHint", bound=Aggregate)
SequenceHint = TypeVar("SequenceHint")


class SnapshotStoreI(Protocol, Generic[IdTypeHint, SequenceHint]):
    @abstractmethod
    def save_snapshots(
        self, snapshots: list[Snapshot], aggregate_id: IdTypeHint
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_last_snapshot(
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


class EventStoreI(Protocol, Generic[SequenceHint, IdTypeHint, AggregateHint]):
    _AggregatedClass: Type[AggregateHint]

    @abstractmethod
    def get_events(
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
    def save_events(self, events: List[Event], aggregate_id: IdTypeHint) -> None:
        """
        Retrieve all events associated with a given aggregate ID.
        This can be useful for historical queries or debugging purposes.
        """
        raise NotImplementedError()

    @contextmanager
    def transaction(self):
        pass

    @abstractmethod
    def save(self, aggregate: AggregateHint) -> None:
        ...

    @abstractmethod
    def load(
        self,
        aggregate_id: IdTypeHint,
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[AggregateHint]:
        ...


class ProjectionStoreI(Protocol, Generic[SequenceHint]):
    @abstractmethod
    def load_projection(
        self,
        aggregate_id: IdTypeHint,
        projection_class: Type[Projection],
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[Projection]:
        ...


class EventStore(
    ABC,
    EventStoreI[SequenceHint, IdTypeHint, AggregateHint],
    ProjectionStoreI[SequenceHint],
    SnapshotStoreI[IdTypeHint, SequenceHint],
):
    def save(self, aggregate: AggregateHint) -> None:
        with self.transaction():
            events_for_save = aggregate.uncommmited_events
            if not events_for_save:
                return

            snapshots = [s for s in events_for_save if isinstance(s, Snapshot)]
            events_without_snapshots = [
                s for s in events_for_save if not isinstance(s, Snapshot)
            ]
            if snapshots:
                self.save_snapshots(snapshots, aggregate.id)
            if events_without_snapshots:
                self.save_events(events_without_snapshots, aggregate.id)
            aggregate.uncommmited_events.clear()

    def load(
        self,
        aggregate_id: IdTypeHint,
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[AggregateHint]:

        snapshot = (
            self.get_last_snapshot(
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
            all_events = self.get_events(
                aggregate_id, lte=load_at, gt=snapshot.sequence_order
            )
        else:
            all_events = self.get_events(aggregate_id, lte=load_at)
            aggregate = self._AggregatedClass(aggregate_id)

            for event in all_events:
                actual_event = event.upcast()
                while not isinstance(actual_event, type(event)):
                    event = actual_event
                    actual_event = event.upcast()
                aggregate._apply_without_saving(actual_event)

        return aggregate

    def load_projection(
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
            self.get_last_snapshot(
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
            all_events = self.get_events(
                aggregate_id, projection_events, lte=load_at, gt=snapshot.sequence_order
            )
        else:
            all_events = self.get_events(aggregate_id, projection_events, lte=load_at)
            aggregate = projection_class(aggregate_id)

        for event in all_events:
            actual_event = event.upcast()
            while not isinstance(actual_event, type(event)):
                event = actual_event
                actual_event = event.upcast()
            aggregate.apply(actual_event)

        return aggregate


# TODO save snapshots on some event
# TODO transaction from up to down

# projection protocol
# snapshot protocol
# aggregate protocol
