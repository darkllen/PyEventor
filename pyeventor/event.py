from __future__ import annotations
from abc import ABC
from typing import TypeVar, Generic, TYPE_CHECKING, Optional, Protocol
from datetime import datetime
import inspect

if TYPE_CHECKING:
    from pyeventor.aggregate import Aggregate, SnapshotCreateI


SequenceHint = TypeVar("SequenceHint")
EventDataTypeHint = TypeVar("EventDataTypeHint")


class SequenceI(Protocol, Generic[SequenceHint]):
    def _sequence_generate(self) -> SequenceHint:
        ...

    @property
    def sequence_order(self) -> SequenceHint:
        ...


class VersionI(Protocol):
    def upcast(self) -> "VersionI":
        return self


class SnapshotI(Protocol):
    @classmethod
    def create(cls, aggregate: SnapshotCreateI) -> "SnapshotI":
        ...


# Abstract class for events
class Event(
    ABC, SequenceI[SequenceHint], VersionI, Generic[SequenceHint, EventDataTypeHint]
):
    def _sequence_generate(self) -> SequenceHint:
        return datetime.now()

    @property
    def sequence_order(self) -> SequenceHint:
        return self._sequence_order

    def __init__(
        self,
        data: Optional[EventDataTypeHint] = None,
        sequence_order: Optional[SequenceHint] = None,
    ):
        self.data = data
        self._sequence_order = sequence_order or self._sequence_generate()


class Snapshot(Event[SequenceHint, EventDataTypeHint], SnapshotI):
    ...


class JsonSnapshot(Snapshot[SequenceHint, dict]):
    @classmethod
    def create(cls, aggregate: SnapshotCreateI):
        attributes = {
            k: v
            for k, v in aggregate.__dict__.items()
            if not k.startswith("_") and not inspect.ismethod(getattr(aggregate, k))
        }
        return JsonSnapshot(data=attributes)


# TODO all fields became a part of event data somehow (?)
# TODO better sequence choosing
