Aggregate
================================================================

This section provide detail information about ``Aggregate``, ``Event`` and their interaction

Create custom aggregate 
****************************************************************

.. code-block:: python

    from pyeventor.aggregate import Aggregate 
    from random import rarandintnd
    class CustomAggregate(Aggregate[int]):
        def _init_empty_attributes(self):
            # this method should be overrided in case of provided attributes to event 
            # to set the default values for them
            # without this it'll be tricky to make a right annotation
            self.attrib: int = 0

        @classmethod
        def _id_factory(cls) -> int:
            # defining the factory for ids.
            # return type should be the same as the generic in the class definition
            # this id will be used to find the aggregate in event store and work with it
            return randint()

    aggregate = CustomAggregate() # _id_factory is ued for id
    aggregate = CustomAggregate(20) # id is provided manually

Create custom event 
****************************************************************

.. code-block:: python

    from pyeventor.event import Event 
    from random import rarandintnd
    from datetime import datetime
    class CustomEvent(Event[int, datetime]):

        def _sequence_generate(self) -> datetime:
            # define the generator for the event sequence
            # according to that it will define the order of events later
            # it should be consistent and provide an order for all the events of the Aggregate
            return datetime.now()
        

    event = CustomEvent(2) # _sequence_generate is ued for sequence_order
    assert event.data == 2

    event = CustomEvent(2, sequence_order=datetime.now()) # sequence_order is provided manually

Set up handlers for events
****************************************************************

The main flow for registration

.. code-block:: python

    from pyeventor.aggregate import Aggregate 
    from pyeventor.event import Event 
    from pyeventor.decorator import register_handler

    class CustomEventA(Event[int, None]):
        ...

    class CustomAggregate(Aggregate[int]):

        @register_handler(CustomEventA) # register from aggregate
        def custom_handler(self, event: CustomEventA):
            ...

    class CustomEventC(Event[int, None]):

        @register_handler(CustomAggregate) # register from event
        def custom_handler(self, aggregate: CustomAggregate):
            ...

    aggregate = CustomAggregate()
    event_a = CustomEventA()
    event_b = CustomEventB()

    aggregate.apply(event_a)
    aagregate.apply(event_b)


The behaviour for event inheritance

.. code-block:: python

    from pyeventor.aggregate import Aggregate 
    from pyeventor.event import Event 
    from pyeventor.decorator import register_handler

    class CustomEventA(Event[int, None]):
        ...

    class CustomEventB(Event[int, None]):
        ...

    class CustomAggregate(Aggregate[int]):

        @register_handler(Event) # use for any event and derived classes
        def custom_handler(self, event: Event):
            ...

        @register_handler(CustomEventA) # use for CustomEventA and derived classes
        def special_custom_handler(self, event: CustomEventA):
            ...


    aggregate = CustomAggregate()
    event_a = CustomEventA()
    event_b = CustomEventB()

    aggregate.apply(event_a) # special_custom_handler will be used as more specific
    aagregate.apply(event_b) # custom_handler will be used as there is no more specific handler


The behaviour for aggregate inheritance

.. code-block:: python

    from pyeventor.aggregate import Aggregate 
    from pyeventor.event import Event 
    from pyeventor.decorator import register_handler

    class CustomEventA(Event[int, None]):
        ...

    class CustomEventB(Event[int, None]):
        ...

    class CustomAggregate(Aggregate[int]):

        @register_handler(CustomEventB)
        def custom_handler(self, event: CustomEventB):
            ...

        @register_handler(CustomEventA)
        def special_custom_handler(self, event: CustomEventA):
            ...

    class CustomDerivedAggregate(CustomAggregate[int]):

        @register_handler(CustomEventB)
        def some_handler(self, event: CustomEventB): 
            ...

        def special_custom_handler(self, event: CustomEventA): # won't be used anyway, as not registered
            ...

    aggregate = CustomDerivedAggregate()
    event_a = CustomEventA()
    event_b = CustomEventB()

    aggregate.apply(event_a) # custom_handler from CustomAggregate will be used
    aagregate.apply(event_b) # some_handler from CustomDerivedAggregate will be used as more specific

the flow for resolving the handlers is:

1. try to find the handler for exact class for exact event
2. try to find the handler for exact class for base of event class
3. get the base of aggregate class and use it to resolve the handling with steps 1-3