from pyeventor.asyncio.aggregate import AsyncAggregate, AsyncProjection
from pyeventor.event import Event, JsonSnapshot
from pyeventor.exceptions import HandlerException
from pyeventor.handler import EventHandler
import inspect


import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
class TestAsyncAggregate:
    @pytest.fixture
    def aggregate_id(self):
        return str(uuid4())

    @pytest.fixture
    def event(self):
        return Event()  # Assuming Event is a simple class or properly mocked

    @pytest.fixture
    def aggregate(self, aggregate_id):
        return AsyncAggregate(aggregate_id)

    def test_init_attributes(self, aggregate, aggregate_id):
        """Test that initial attributes are set correctly."""
        assert aggregate.id == aggregate_id

    @patch("pyeventor.handler.EventHandler.get_handler")
    async def test_apply_without_saving_valid_event(
        self, mock_get_handler, aggregate, event
    ):
        """Test applying an event that has a registered handler."""
        handler = AsyncMock()
        mock_get_handler.return_value = handler

        result = await aggregate.apply(event)

        handler.assert_called_once_with(aggregate, event)
        assert event in aggregate._pending_events
        assert aggregate._events_applied == 1
        assert result == aggregate

    @patch("pyeventor.handler.EventHandler.get_handler", return_value=None)
    async def test_apply_without_saving_invalid_event(
        self, mock_get_handler, aggregate, event
    ):
        """Test applying an event that has no registered handler."""
        with pytest.raises(HandlerException):
            await aggregate.apply(event)


@pytest.mark.asyncio
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
        return AsyncProjection(projection_id)

    def test_projection_init(self, projection, projection_id):
        """Test that projection initialization sets the ID correctly."""
        assert projection.id == projection_id

    @patch("pyeventor.handler.EventHandler.get_handler")
    async def test_projection_apply_valid_event(
        self, mock_get_handler, projection, event
    ):
        """Test applying an event that has a registered handler in the projection."""
        handler = AsyncMock()
        mock_get_handler.return_value = handler

        result = await projection.apply(event)

        handler.assert_called_once_with(projection, event)
        assert result == projection

    @patch("pyeventor.handler.EventHandler.get_handler", return_value=None)
    async def test_projection_apply_invalid_event(
        self, mock_get_handler, projection, event
    ):
        """Test applying an event that has no registered handler in the projection."""
        with pytest.raises(HandlerException):
            await projection.apply(event)
