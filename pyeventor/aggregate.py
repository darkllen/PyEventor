from abc import ABC
from pyeventor.event import Event, Snapshot, JsonSnapshot, SnapshotI
from uuid import uuid4
from pyeventor.exceptions import HandlerException
from typing import Generic, TypeVar, Optional, Protocol, Type
from pyeventor.handler import EventHandler
import inspect
from abc import abstractmethod

IdTypeHint = TypeVar("IdTypeHint")


class AttributesI(Protocol, Generic[IdTypeHint]):
    @classmethod
    def _id_factory(cls) -> IdTypeHint:
        return str(uuid4())

    def _init_attributes(self, aggregate_id: Optional[IdTypeHint] = None):
        self._init_empty_attributes()
        self._aggregate_id = aggregate_id or self._id_factory()

    def _init_empty_attributes(self):
        ...

    @property
    def id(self) -> IdTypeHint:
        return self._aggregate_id


class ApplyI(Protocol):
    def _apply_without_saving(self, event: Event) -> "ApplyI":
        if handler := EventHandler.get_handler(type(self), type(event)):
            handler(self, event)
            return self
        raise HandlerException(f"handler for {event.__class__.__name__} not found")

    @abstractmethod
    def apply(self, event: Event) -> "ApplyI":
        ...


class SnapshotFromI(Protocol, Generic[IdTypeHint]):
    SnapshotClass: Type[Snapshot] = Snapshot

    @classmethod
    @abstractmethod
    def from_snapshot(
        cls, aggregate_id: IdTypeHint, snapshot: Snapshot
    ) -> "SnapshotFromI":
        ...


class SnapshotFromJsonI(Protocol[IdTypeHint]):
    SnapshotClass: Type[JsonSnapshot] = JsonSnapshot

    @classmethod
    def from_snapshot(
        cls, aggregate_id: IdTypeHint, snapshot: SnapshotClass
    ) -> "Aggregate":
        obj = cls(aggregate_id)
        for k, v in snapshot.data.items():
            setattr(obj, k, v)
        return obj


class SnapshotCreateI(SnapshotFromI[IdTypeHint]):
    projection_snapshot_classes: list[Type[Snapshot]] = []

    @abstractmethod
    def create_snapshot(self) -> Snapshot:
        ...


class SnapshotCreateJsonI(SnapshotFromJsonI[IdTypeHint], SnapshotCreateI[IdTypeHint]):
    def create_snapshot(self) -> JsonSnapshot:
        attributes = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and not inspect.ismethod(getattr(self, k))
        }
        return JsonSnapshot(data=attributes)


class Aggregate(
    ABC,
    AttributesI[IdTypeHint],
    ApplyI,
    SnapshotCreateJsonI[IdTypeHint],
):
    @property
    def uncommmited_events(self) -> list[Event]:
        return self._pending_events

    def __init__(
        self,
        aggregate_id: Optional[IdTypeHint] = None,
        auto_snapshot_each_n: Optional[int] = None,
    ):
        super()._init_attributes(aggregate_id)
        self._auto_snapshot_each_n = auto_snapshot_each_n
        self._events_applied = 0
        self._pending_events: list[Event] = []

    def apply(self, event: Event) -> "Aggregate":
        self._apply_without_saving(event)
        self._events_applied += 1
        self._pending_events.append(event)
        if (
            self._auto_snapshot_each_n
            and self._events_applied % self._auto_snapshot_each_n == 0
        ):
            snapshots = []
            snapshots.append(self.SnapshotClass.create(self))
            for snapshot_projection in self.projection_snapshot_classes:
                snapshots.append(snapshot_projection.create(self))
            self._pending_events.extend(snapshots)
        return self


class Projection(ABC, AttributesI[IdTypeHint], ApplyI, SnapshotFromJsonI[IdTypeHint]):
    def __init__(self, aggregate_id: Optional[IdTypeHint] = None):
        super()._init_attributes(aggregate_id)

    def apply(self, event: Event) -> "Projection":
        self._apply_without_saving(event)
        return self


# TODO prevent using AggregateB as AggregateA (introducing create event with type of aggregate)
