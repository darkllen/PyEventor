from abc import ABC, abstractmethod
from pyeventor.event import Event, Snapshot, JsonSnapshot, SnapshotI
from uuid import uuid4
from pyeventor.exceptions import HandlerException
from typing import Generic, TypeVar, Optional, Protocol, Type
from pyeventor.handler import EventHandler
import inspect
from pyeventor.aggregate import (
    AttributesI,
    SnapshotFromJsonI,
    SnapshotCreateI,
    IdTypeHint,
    SnapshotCreateJsonI,
)


class ApplyAsyncI(Protocol):
    async def _apply_without_saving(self, event: Event) -> "ApplyAsyncI":
        if handler := EventHandler.get_handler(type(self), type(event)):
            await handler(self, event)
            return self
        raise HandlerException(f"handler for {event.__class__.__name__} not found")

    @abstractmethod
    async def apply(self, event: Event) -> "ApplyAsyncI":
        ...


class AsyncAggregate(
    ABC,
    AttributesI[IdTypeHint],
    ApplyAsyncI,
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

    async def apply(self, event: Event) -> "Aggregate":
        await self._apply_without_saving(event)
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


class AsyncProjection(
    ABC, AttributesI[IdTypeHint], ApplyAsyncI, SnapshotFromJsonI[IdTypeHint]
):
    def __init__(self, aggregate_id: Optional[IdTypeHint] = None):
        super()._init_attributes(aggregate_id)

    async def apply(self, event: Event) -> "Projection":
        await self._apply_without_saving(event)
        return self
