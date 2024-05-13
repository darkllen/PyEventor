from pyeventor.event import Event
from pyeventor.aggregate import Aggregate, Projection
from pyeventor.exceptions import RegisterException
from pyeventor.handler import EventHandler


from typing import Union, Type, Callable


def register_handler(*register_objects: Union[Type[Event], Type[Aggregate]]):
    class wrapper:
        def __init__(self, handler: Callable):
            self.handler = handler

        def __set_name__(
            self, handler_class: Union[Type[Event], Type[Aggregate]], name: str
        ):
            if all(
                map(
                    lambda x: isinstance(x, type) and issubclass(x, Event),
                    register_objects,
                )
            ):
                class_handlers = EventHandler.get_aggregate_handlers(handler_class)
                for event_class in register_objects:
                    existed_handler = class_handlers.get(event_class)
                    if (
                        existed_handler
                        and existed_handler.__qualname__ != self.handler.__qualname__
                    ):
                        raise RegisterException(
                            "Register of the same event more than once for the same class is not allowed"
                        )
                    EventHandler.set_handler(handler_class, event_class, self.handler)
            elif all(
                map(
                    lambda x: isinstance(x, type) and issubclass(x, Aggregate),
                    register_objects,
                )
            ):
                for aggregate_class in register_objects:
                    class_handlers = EventHandler.get_aggregate_handlers(
                        aggregate_class
                    )
                    existed_handler = class_handlers.get(handler_class)

                    if (
                        existed_handler
                        and existed_handler.__qualname__ != self.handler.__qualname__
                    ):
                        raise RegisterException(
                            "Register of the same event more than once for the same class is not allowed"
                        )
                    EventHandler.set_handler(
                        aggregate_class, handler_class, self.handler
                    )
            else:
                raise RegisterException(
                    "all register_objects should be the same Event or Aggregate class"
                )

            setattr(handler_class, name, self.handler)

    return wrapper


def projection(aggregate_class: Type[Aggregate], events: list[Type[Event]]):
    def wrapper(projection_class: Type[Projection]):
        if (
            projection_class.SnapshotClass
            not in aggregate_class.projection_snapshot_classes
        ):
            aggregate_class.projection_snapshot_classes.append(
                projection_class.SnapshotClass
            )

        for event_class in events:
            inherited_handler = EventHandler.get_handler(aggregate_class, event_class)
            if not EventHandler.get_handler(projection_class, event_class):
                EventHandler.set_handler(
                    projection_class, event_class, inherited_handler
                )

        return projection_class

    return wrapper


# TODO restrict projection registrate extra event handlers
