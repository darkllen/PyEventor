import pytest
from unittest.mock import MagicMock, patch

# Assuming these imports are from your project's modules
from pyeventor.event import Event
from pyeventor.aggregate import Aggregate, Projection
from pyeventor.handler import EventHandler
from pyeventor.exceptions import RegisterException
from pyeventor.decorator import register_handler, projection


class TestRegisterHandler:
    # Mock classes
    class MockEvent1(Event):
        pass

    class MockEvent2(Event):
        pass

    class MockAggregate1(Aggregate):
        pass

    class MockAggregate2(Aggregate):
        pass

    def mock_handler(self):
        ...

    @pytest.fixture
    def mock_get_aggregate_handlers(self):
        with patch(
            "pyeventor.handler.EventHandler.get_aggregate_handlers", return_value={}
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_set_handler(self):
        with patch("pyeventor.handler.EventHandler.set_handler") as mock:
            yield mock

    def test_register_single_event_handler(
        self, mock_get_aggregate_handlers, mock_set_handler
    ):
        """Test registering a handler for a single event type."""

        class MockAggregate1(Aggregate):
            @register_handler(self.MockEvent1)
            def handle_event(self):
                pass

        mock_set_handler.assert_called_once_with(
            MockAggregate1, self.MockEvent1, MockAggregate1.handle_event
        )
        assert hasattr(MockAggregate1, "handle_event")

    def test_register_multiple_event_handlers_failure_due_to_mixed_types(self):
        """Test that registering mixed types (Event and Aggregate) raises an exception."""
        with pytest.raises(RuntimeError) as e:

            class MockAggregate1(Aggregate):
                @register_handler(self.MockEvent1, self.MockAggregate2)
                def handle_event(self):
                    pass

            assert type(e.__cause__) == RegisterException

    def test_register_duplicate_event_handler_raises_exception(
        self, mock_get_aggregate_handlers
    ):
        """Test that registering the same event handler more than once raises an exception."""
        mock_get_aggregate_handlers.return_value = {self.MockEvent1: self.mock_handler}

        with pytest.raises(RuntimeError) as e:

            class MockAggregate1(Aggregate):
                @register_handler(self.MockEvent1)
                def handle_event(self):
                    pass

            assert type(e.__cause__) == RegisterException

    def test_register_event_handler_to_multiple_events(
        self, mock_get_aggregate_handlers, mock_set_handler
    ):
        """Test registering a handler to multiple events of the same type."""

        class MockAggregate1(Aggregate):
            @register_handler(self.MockEvent1, self.MockEvent2)
            def handle_event(self):
                pass

        assert mock_set_handler.call_count == 2
        mock_set_handler.assert_any_call(
            MockAggregate1, self.MockEvent1, MockAggregate1.handle_event
        )
        mock_set_handler.assert_any_call(
            MockAggregate1, self.MockEvent2, MockAggregate1.handle_event
        )
        assert hasattr(MockAggregate1, "handle_event")


class TestProjection:

    # Mock classes
    class MockEvent1(Event):
        pass

    class MockEvent2(Event):
        pass

    class MockAggregate(Aggregate):
        projection_snapshot_classes = []

        class MockEvent3(Event):
            pass

        @register_handler(MockEvent3)
        def some(self):
            ...

    class MockProjection(Projection):
        SnapshotClass = MagicMock()

    class MockSnapshot:
        pass

    @pytest.fixture
    def mock_get_handler(self):
        with patch(
            "pyeventor.handler.EventHandler.get_handler", return_value=MagicMock()
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_set_handler(self):
        with patch("pyeventor.handler.EventHandler.set_handler") as mock:
            yield mock

    def test_projection_decorator_registers_snapshot_class(self):
        """Test that the projection decorator correctly registers the projection snapshot class with the aggregate."""
        assert (
            self.MockProjection.SnapshotClass
            not in self.MockAggregate.projection_snapshot_classes
        )

        @projection(self.MockAggregate, [self.MockEvent1])
        class EnhancedProjection(self.MockProjection):
            pass

        assert (
            self.MockProjection.SnapshotClass
            in self.MockAggregate.projection_snapshot_classes
        )

    def test_projection_decorator_inherits_event_handlers(
        self, mock_get_handler, mock_set_handler
    ):
        """Test that the projection decorator inherits event handlers from the aggregate when not set on the projection."""
        # Setup an inherited handler
        handler = MagicMock()
        mock_get_handler.return_value = handler

        @projection(
            self.MockAggregate, [self.MockEvent1, self.MockAggregate.MockEvent3]
        )
        class AnotherProjection(self.MockProjection):
            pass

        assert mock_get_handler.call_count == 4  # Called twice, once for each event
        mock_get_handler.assert_any_call(self.MockAggregate, self.MockEvent1)
        mock_get_handler.assert_any_call(
            self.MockAggregate, self.MockAggregate.MockEvent3
        )
        mock_set_handler.assert_not_called()  # Handlers set from
        assert (
            EventHandler.get_handler(AnotherProjection, self.MockAggregate.MockEvent3)
            == handler
        )

    def test_no_duplicate_handler_registration(
        self, mock_get_handler, mock_set_handler
    ):
        """Test that the projection decorator does not register a handler if it already exists on the projection."""
        # Return a handler if asked for the projection directly to simulate pre-existing registration

        @projection(self.MockAggregate, [self.MockAggregate.MockEvent3])
        class AnotherProjection(self.MockProjection):
            @register_handler(self.MockAggregate.MockEvent3)
            def some(self):
                ...

        mock_get_handler.assert_called_with(
            AnotherProjection, self.MockAggregate.MockEvent3
        )
        mock_set_handler.assert_called_once_with(
            AnotherProjection, self.MockAggregate.MockEvent3, AnotherProjection.some
        )  # Ensure no handler was set since it already exists
