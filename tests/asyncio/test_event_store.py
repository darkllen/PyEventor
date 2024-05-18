import pytest
from unittest.mock import patch

# Assuming these imports are from your project's modules
from pyeventor.event import Event, Snapshot
from pyeventor.asyncio.aggregate import AsyncAggregate, AsyncProjection
from pyeventor.asyncio.event_store import AsyncEventStore
from contextlib import asynccontextmanager


class MockEvent(Event):
    pass


class MockSnapshot(Snapshot):
    pass


class MockAggregate(AsyncAggregate):
    SnapshotClass = MockSnapshot


class ConcreteEventStore(AsyncEventStore):
    _AggregatedClass = MockAggregate

    @asynccontextmanager
    async def transaction(self):
        yield


@pytest.fixture
def mock_aggregate():
    aggregate = MockAggregate(aggregate_id="test_id")
    aggregate._pending_events = [MockEvent(), MockSnapshot()]
    return aggregate


@pytest.fixture
def mock_projection():
    class MockProjection(AsyncProjection):
        SnapshotClass = MockSnapshot

    return MockProjection


@pytest.mark.asyncio
class TestEventStore:
    @patch.multiple(ConcreteEventStore, __abstractmethods__=set())
    async def test_transaction_management(self):
        event_store = ConcreteEventStore()
        async with event_store.transaction():
            pass

    @patch.multiple(ConcreteEventStore, __abstractmethods__=set())
    async def test_save_no_events(self, mock_aggregate):
        event_store = ConcreteEventStore()
        mock_aggregate._pending_events = []
        with patch.object(event_store, "save_events") as mock_save_events, patch.object(
            event_store, "save_snapshots"
        ) as mock_save_snapshots:
            await event_store.save(mock_aggregate)
            mock_save_events.assert_not_called()
            mock_save_snapshots.assert_not_called()

    @patch.multiple(ConcreteEventStore, __abstractmethods__=set())
    async def test_save_with_events_and_snapshots(self, mock_aggregate):
        event_store = ConcreteEventStore()
        with patch.object(event_store, "save_events") as mock_save_events, patch.object(
            event_store, "save_snapshots"
        ) as mock_save_snapshots:
            await event_store.save(mock_aggregate)
            mock_save_events.assert_called_once()
            mock_save_snapshots.assert_called_once()

    @patch.multiple(ConcreteEventStore, __abstractmethods__=set())
    async def test_load_aggregate_from_snapshot(self):
        event_store = ConcreteEventStore()
        with patch.object(
            event_store, "get_last_snapshot"
        ) as mock_get_last_snapshot, patch.object(
            event_store, "get_events"
        ) as mock_get_events, patch.object(
            MockAggregate, "from_snapshot"
        ) as mock_from_snapshot:
            mock_get_last_snapshot.return_value = MockSnapshot()
            await event_store.load("test_id")
            mock_get_last_snapshot.assert_called_once()
            mock_get_events.assert_called_once()
            mock_from_snapshot.assert_called_once()

    @patch.multiple(ConcreteEventStore, __abstractmethods__=set())
    async def test_load_projection(self, mock_projection):
        event_store = ConcreteEventStore()
        with patch.object(
            event_store, "get_last_snapshot"
        ) as mock_get_last_snapshot, patch.object(
            event_store, "get_events"
        ) as mock_get_events, patch.object(
            mock_projection, "from_snapshot"
        ) as mock_from_snapshot:
            mock_get_last_snapshot.return_value = MockSnapshot()
            await event_store.load_projection("test_id", mock_projection)
            mock_get_last_snapshot.assert_called_once()
            mock_get_events.assert_called_once()
            mock_from_snapshot.assert_called_once()
