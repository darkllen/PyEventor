Event Store
================================================================

``EventStore`` define the interface for the interaction with storage
abstract methods should be implemented for that

Define the implementation 
****************************************************************

.. code-block:: python

    class CustomEventStore(EventStore[AggregateHint, SequenceHint, IdTypeHint]): # class of Aggregate, sequence type, id type are the generics

        def get_events(
            self,
            aggregate_id: IdTypeHint,
            event_types: list[Type[Event]] = [],
            gt: Optional[SequenceHint] = None,
            lte: Optional[SequenceHint] = None,
        ) -> List[Event]:
            # get all the events of certain type for the aggregate with aggregate_id 
            # ehich sequence_order is greater of gt and less or equal of lte

        def save_events(self, events: List[Event], aggregate_id: IdTypeHint) -> None:
            # save all the events in a such way, that they will be queryable by get_events method

        @contextmanager
        def transaction(self):
            # provide a transaction that will be used in save_events to save only all the events together

        def save_snapshots(
            self, snapshots: list[Snapshot], aggregate_id: IdTypeHint
        ) -> None:
            # save snapshots. Separate method to provide separation beetween events and snapshot storage

        def get_last_snapshot(
            self,
            aggregate_id: IdTypeHint,
            snapshot_type: Optional[Type[Snapshot]] = None,
            load_at: Optional[SequenceHint] = None,
        ) -> Optional[Snapshot]:
            # get last snapshot for the aggregate_id of the certain type which sequence_order is less than load_at

Usage 
****************************************************************

.. code-block:: python
    
    class AggregateCustomEventStore(CustomEventStore[CustomAggregate, int, str]):
        _AggregatedClass = CustomAggregate

    some_aggregate: CustomAggregate
    projection: CustomProjection

    storage = AggregateCustomEventStore()

    storage.save(some_aggregate)
    storage.load(some_aggregate_id)
    storage.load_projection(some_aggregate_id, CustomProjection)
    storage.load(some_aggregate_id, load_at=5) # load at the certain moment
