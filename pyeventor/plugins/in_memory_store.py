from pyeventor.event_store import (
    EventStore,
    IdTypeHint,
    SequenceHint,
    Event,
    Snapshot,
    AggregateHint,
)
from typing import Type, List, Optional, Generic
from datetime import datetime
from contextlib import contextmanager


class InMemoryEventStore(EventStore[AggregateHint, SequenceHint, IdTypeHint]):
    def __init__(self):
        self.events = {}
        self.snapshots = {}

    def get_events(
        self,
        aggregate_id: IdTypeHint,
        event_types: list[Type[Event]] = [],
        gt: Optional[SequenceHint] = None,
        lte: Optional[SequenceHint] = None,
    ) -> List[Event]:
        if aggregate_id in self.events:
            events = self.events[aggregate_id]
            if event_types:
                events = [
                    event
                    for event in events
                    if isinstance(event[1], tuple(event_types))
                ]
            if gt:
                events = [event for event in events if event[1].sequence_order > gt]
            if lte:
                events = [event for event in events if event[1].sequence_order <= lte]
            return [event[1] for event in events]
        return []

    def save_events(self, events: List[Event], aggregate_id: IdTypeHint) -> None:
        if aggregate_id not in self.events:
            self.events[aggregate_id] = []
        for event in events:
            self.events[aggregate_id].append((type(event), event))

    @contextmanager
    def transaction(self):
        yield

    def save_snapshots(
        self, snapshots: list[Snapshot], aggregate_id: IdTypeHint
    ) -> None:
        if aggregate_id not in self.snapshots:
            self.snapshots[aggregate_id] = []
        for snapshot in snapshots:
            self.snapshots[aggregate_id].append((type(snapshot), snapshot))

    def get_last_snapshot(
        self,
        aggregate_id: IdTypeHint,
        snapshot_type: Optional[Type[Snapshot]] = None,
        load_at: Optional[SequenceHint] = None,
    ) -> Optional[Snapshot]:
        if aggregate_id in self.snapshots:
            snapshots = self.snapshots[aggregate_id]
            if snapshot_type:
                snapshots = [s for s in snapshots if isinstance(s[1], snapshot_type)]
            if load_at:
                snapshots = [s for s in snapshots if s[1].sequence_order <= load_at]
            if snapshots:
                return snapshots[-1][1]
        return None, None
