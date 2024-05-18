Start
================================================================

Defining the aggregate and define its possible attributes
****************************************************************

.. code-block:: python

    from pyeventor.aggregate import Aggregate 
    class CustomAggregate(Aggregate[str]):
        def _init_empty_attributes(self):
            self.attrib: int = None

Generic of the aggregate defining the type of id that will be used for aggregate.
For more details see the :ref:`Aggregate`

Defining the event
****************************************************************



.. code-block:: python

    from pyeventor.event import Event
    class CustomEvent(Event[int, int]):
        ...

First event generic define the sequence type, that will be used for events ordering (datetime by default)
Second event generic define the data type that will be stored in the event. It can be any object.
For more details see the :ref:`Aggregate`

Register handler for process the event
****************************************************************

.. code-block:: python

    from pyeventor.aggregate import Aggregate 
    class CustomAggregate(Aggregate[str]):
        @register_handler(CustomEvent)
        def event_handler(self, event: CustomEvent):
            self.attrib = event.data # int expected as datatype specified as int

With such an example we can specify the method which will be called on event processing.
For more details on event handling, see the :ref:`Aggregate`

Create the event store
****************************************************************


To create event store methods for working with events should be implemented

.. code-block:: python

    from pyeventor.event_store import (
        EventStore,
        IdTypeHint,
        SequenceHint,
        Event,
        AggregateHint,
    )
    class CustomEventStore(EventStore[AggregateHint, SequenceHint, IdTypeHint]):
        def get_events(
            self,
            aggregate_id: IdTypeHint,
            event_types: list[Type[Event]] = [],
            gt: Optional[SequenceHint] = None,
            lte: Optional[SequenceHint] = None,
        ) -> List[Event]:
            ...
        
        def save_events(self, events: List[Event], aggregate_id: IdTypeHint) -> None:
            ...

        def save_snapshots(
            self, snapshots: list[Snapshot], aggregate_id: IdTypeHint
        ) -> None:
            ...

        def get_last_snapshot(
                self,
                aggregate_id: IdTypeHint,
                snapshot_type: Optional[Type[Snapshot]] = None,
                load_at: Optional[SequenceHint] = None,
            ) -> Optional[Snapshot]:

Based on them all other methods are implemented:

.. code-block:: python

    def save(self, aggregate: AggregateHint) -> None
    def load(
        self,
        aggregate_id: IdTypeHint,
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[AggregateHint]
    def load_projection(
        self,
        aggregate_id: IdTypeHint,
        projection_class: Type[Projection],
        load_at: Optional[SequenceHint] = None,
        from_snapshots: bool = True,
    ) -> Optional[Projection]:

Detailed usage and examples of implenetation can be found in :ref:`Examples`


Example of usage
********************************

.. code-block:: python

    aggregate = CustomAggregate()
    event = CustomEvent(2)

    aggregate.apply(event)

    storage = CustomEventStore()
    storage.save(aggregate)
    storage.load(aggregate.id)
