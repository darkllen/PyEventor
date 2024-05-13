from datetime import datetime, timedelta
import pytest
from unittest.mock import MagicMock
from pyeventor.event import Event, JsonSnapshot

# Assuming the classes Event, JsonSnapshot, and others are imported correctly


class TestEvent:
    @pytest.fixture
    def event_data(self):
        return {"key": "value"}

    @pytest.fixture
    def event(self, event_data):
        return Event(data=event_data)

    @pytest.fixture
    def aggregate_mock(self):
        aggregate = MagicMock()

        aggregate.__dict__ = {
            "attribute1": "value1",
            "attribute2": "value2",
            "_private": "should not be included",
        }
        return aggregate

    def test_event_sequence_generation(self, event):
        """Test that the event sequence is generated correctly."""
        assert isinstance(
            event.sequence_order, datetime
        ), "Sequence order should be a datetime object"

    def test_event_custom_sequence(self):
        """Test event initialization with custom sequence order."""
        custom_time = datetime.now() - timedelta(days=1)
        custom_event = Event(sequence_order=custom_time)
        assert (
            custom_event.sequence_order == custom_time
        ), "Custom sequence order should be set correctly"

    def test_event_upcast(self):
        """Test that the upcast method returns the same event instance."""
        event_instance = Event()
        upcasted_event = event_instance.upcast()
        assert (
            upcasted_event is event_instance
        ), "Upcast should return the same event instance"

    def test_json_snapshot_creation(self, aggregate_mock):
        """Test that JsonSnapshot.create correctly extracts attributes to include in the snapshot."""
        snapshot = JsonSnapshot.create(aggregate_mock)
        expected_data = {"attribute1": "value1", "attribute2": "value2"}
        assert (
            snapshot.data == expected_data
        ), "Snapshot should only contain public attributes that aren't methods"
