from pyeventor.aggregate import Aggregate, Projection
from pyeventor.event import Event, JsonSnapshot
from pyeventor.exceptions import HandlerException
from pyeventor.handler import EventHandler
import inspect


import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock


class TestAggregate:
    @pytest.fixture
    def aggregate_id(self):
        return str(uuid4())

    @pytest.fixture
    def event(self):
        return Event()  # Assuming Event is a simple class or properly mocked

    @pytest.fixture
    def snapshot(self):
        return JsonSnapshot(
            data={"attribute1": "value1", "attribute2": "value2"}
        )  # Example JsonSnapshot

    @pytest.fixture
    def aggregate(self, aggregate_id):
        return Aggregate(aggregate_id)

    def test_init_attributes(self, aggregate, aggregate_id):
        """Test that initial attributes are set correctly."""
        assert aggregate.id == aggregate_id

    @patch("pyeventor.handler.EventHandler.get_handler")
    def test_apply_without_saving_valid_event(self, mock_get_handler, aggregate, event):
        """Test applying an event that has a registered handler."""
        handler = MagicMock()
        mock_get_handler.return_value = handler

        result = aggregate.apply(event)

        handler.assert_called_once_with(aggregate, event)
        assert event in aggregate._pending_events
        assert aggregate._events_applied == 1
        assert result == aggregate

    @patch("pyeventor.handler.EventHandler.get_handler", return_value=None)
    def test_apply_without_saving_invalid_event(
        self, mock_get_handler, aggregate, event
    ):
        """Test applying an event that has no registered handler."""
        with pytest.raises(HandlerException):
            aggregate.apply(event)

    def test_create_snapshot(self, aggregate):
        """Test creating a snapshot from aggregate state."""
        snapshot = aggregate.create_snapshot()

        expected_data = {
            k: v
            for k, v in aggregate.__dict__.items()
            if not k.startswith("_") and not inspect.ismethod(getattr(aggregate, k))
        }
        assert snapshot.data == expected_data

    @patch("pyeventor.handler.EventHandler.get_handler")
    def test_automatic_snapshot_creation(self, mock_get_handler, aggregate_id):
        """Test automatic snapshot creation after a specified number of events."""
        n = 5  # Set auto snapshot every 5 events
        aggregate = Aggregate(aggregate_id, auto_snapshot_each_n=n)
        events = [Event() for _ in range(n)]

        for event in events:
            aggregate.apply(event)

        assert len(aggregate._pending_events) == n + 1  # n events + 1 snapshot
        assert isinstance(aggregate._pending_events[-1], JsonSnapshot)

    def test_from_snapshot(self, aggregate_id, snapshot):
        """Test loading an aggregate from a snapshot."""
        with patch.object(Aggregate, "__init__", return_value=None) as mock_init:
            # Patch __init__ to not execute during this test
            aggregate = Aggregate.from_snapshot(aggregate_id, snapshot)
            mock_init.assert_called_once_with(aggregate_id)

            # Ensure attributes are correctly set from snapshot
            for k, v in snapshot.data.items():
                assert getattr(aggregate, k) == v


class TestProjection:
    @pytest.fixture
    def projection_id(self):
        return str(uuid4())

    @pytest.fixture
    def event(self):
        return Event()  # Assuming Event is a simple class or properly mocked

    @pytest.fixture
    def snapshot(self):
        return JsonSnapshot(
            data={"attribute1": "value1", "attribute2": "value2"}
        )  # Example JsonSnapshot

    @pytest.fixture
    def projection(self, projection_id):
        return Projection(projection_id)

    def test_projection_init(self, projection, projection_id):
        """Test that projection initialization sets the ID correctly."""
        assert projection.id == projection_id

    @patch("pyeventor.handler.EventHandler.get_handler")
    def test_projection_apply_valid_event(self, mock_get_handler, projection, event):
        """Test applying an event that has a registered handler in the projection."""
        handler = MagicMock()
        mock_get_handler.return_value = handler

        result = projection.apply(event)

        handler.assert_called_once_with(projection, event)
        assert result == projection

    @patch("pyeventor.handler.EventHandler.get_handler", return_value=None)
    def test_projection_apply_invalid_event(self, mock_get_handler, projection, event):
        """Test applying an event that has no registered handler in the projection."""
        with pytest.raises(HandlerException):
            projection.apply(event)

    def test_projection_from_snapshot(self, projection_id, snapshot):
        """Test loading a projection from a snapshot."""
        with patch.object(Projection, "__init__", return_value=None) as mock_init:
            # Patch __init__ to not execute during this test
            projection = Projection.from_snapshot(projection_id, snapshot)
            mock_init.assert_called_once_with(projection_id)

            # Ensure attributes are correctly set from snapshot
            for k, v in snapshot.data.items():
                assert getattr(projection, k) == v
