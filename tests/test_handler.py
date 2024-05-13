import pytest
from unittest.mock import MagicMock

# Assuming these imports are from your project's modules
from pyeventor.event import Event
from pyeventor.aggregate import Aggregate
from pyeventor.handler import EventHandler
from collections import defaultdict


class TestEventHandler:

    # Mock classes for events and aggregates
    class BaseEvent(Event):
        pass

    class DerivedEvent(BaseEvent):
        pass

    class BaseAggregate(Aggregate):
        pass

    class DerivedAggregate(BaseAggregate):
        pass

    # Mock handler function
    def base_event_handler(self, aggregate, event):
        pass

    def derived_event_handler(self, aggregate, event):
        pass

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        # Code that will run before your test, for example:
        EventHandler.__event_handlers__ = defaultdict(dict)
        # A test function will be run at this point
        yield

    def test_set_handler(self):
        """Test setting an event handler."""
        EventHandler.set_handler(
            self.BaseAggregate, self.BaseEvent, self.base_event_handler
        )
        assert (
            EventHandler.__event_handlers__[self.BaseAggregate][self.BaseEvent]
            == self.base_event_handler
        )

    def test_get_handler_direct_match(self):
        """Test retrieving an event handler with a direct class match."""
        EventHandler.set_handler(
            self.BaseAggregate, self.BaseEvent, self.base_event_handler
        )
        handler = EventHandler.get_handler(self.BaseAggregate, self.BaseEvent)
        assert handler == self.base_event_handler

    def test_get_handler_with_inheritance(self):
        """Test retrieving an event handler via class inheritance."""
        EventHandler.set_handler(
            self.BaseAggregate, self.BaseEvent, self.base_event_handler
        )
        handler = EventHandler.get_handler(self.DerivedAggregate, self.DerivedEvent)
        assert (
            handler == self.base_event_handler
        ), "Handler should be inherited from base classes"

    def test_get_handler_no_match(self):
        """Test that retrieving an event handler returns None when no handler is available."""
        handler = EventHandler.get_handler(self.BaseAggregate, self.DerivedEvent)
        assert handler is None, "Should return None if no handler is set"

    def test_copy_handlers(self):
        """Test copying handlers from one aggregate type to another."""
        EventHandler.set_handler(
            self.BaseAggregate, self.BaseEvent, self.base_event_handler
        )
        EventHandler.copy_handlers(self.BaseAggregate, self.DerivedAggregate)
        assert (
            EventHandler.get_handler(self.DerivedAggregate, self.BaseEvent)
            == self.base_event_handler
        )
