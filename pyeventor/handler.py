from __future__ import annotations
from collections import defaultdict

import inspect
from typing import Type, Callable, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyeventor.aggregate import Aggregate
    from pyeventor.event import Event


class EventHandler:
    __event_handlers__: dict[Type, dict[Type, Callable]] = defaultdict(dict)

    @classmethod
    def set_handler(
        cls,
        aggregate_class: Type[Aggregate],
        event_class: Type[Event],
        function: Callable,
    ) -> None:
        cls.__event_handlers__[aggregate_class][event_class] = function

    @classmethod
    def get_aggregate_handlers(
        cls, aggregate_class: Type[Aggregate]
    ) -> dict[Type, Callable]:
        return cls.__event_handlers__.get(aggregate_class, {})

    @classmethod
    def get_handler(
        cls, aggregate_class: Type[Aggregate], event_class: Type[Event]
    ) -> Optional[Callable]:
        for next_class_base in inspect.getmro(aggregate_class):
            class_handlers = cls.get_aggregate_handlers(next_class_base)
            for next_event_base in inspect.getmro(event_class):
                if handler := class_handlers.get(next_event_base):
                    return handler
        return None

    @classmethod
    def copy_handlers(
        cls, copy_from: Type[Aggregate], copy_to: Type[Aggregate]
    ) -> None:
        cls.__event_handlers__[copy_to] = cls.get_aggregate_handlers(copy_from)

    @classmethod
    def get_event_class_by_name(cls, event_class_name: str) -> Type[Event]:
        for event_dict in cls.__event_handlers__.values():
            for event_class in event_dict.keys():
                if event_class.__name__ == event_class_name:
                    return event_class
        return None


# TODO change back to names from classes as more stable option
