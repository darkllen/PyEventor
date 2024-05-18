Snapshot
================================================================

``Snapshot`` is event that provide the latest information about the ``Aggregate``` so we can not query the events before it

Define the Snapshot
****************************************************************

.. code-block:: python

    from pyeventor.aggregate import Aggregate, Projection
    from pyeventor.event import Event 
    from pyeventor.decorator import register_handler, projection

    class CustomEventA(Event[int, None]):
        ...

    class CustomEventB(Event[int, None]):
        ...

    class CustomAggregate(Aggregate[int]):
        SnapshotClass = JsonSnapshot # define the snapshot class, JsonSnapshot is a default one

        @register_handler(CustomEventB)
        def custom_handler(self, event: CustomEventB):
            ...

        @register_handler(CustomEventA)
        def special_custom_handler(self, event: CustomEventA):
            ...

    aagregate = CustomAggregate(auto_snapshot_each_n=2) # each two events, snapshots will be created
    event_a = CustomEventA()
    event_b = CustomEventB()

    aggregate.apply(event_a)
    aagregate.apply(event_b) # after that event, snapshot will be created
    aggregate.apply(event_a)

    storage = CustomEventStore()
    storage.save(aggregate) # snpahot is saved among with other events
    storage.load(aggregate.id) # loaded with snapshot (only the last event will be applied as it was done after the snpahot)
    storage.load(aggregate.id, from_snapshots=False) # loaded without snapshots


Define the Partial Snapshot
****************************************************************

It's possible to create snpahot not for the full ``Aggregate`` but for it's ``Projection``

.. code-block:: python

    from pyeventor.aggregate import Aggregate, Projection
    from pyeventor.event import Event 
    from pyeventor.decorator import register_handler, projection

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

    @projection(CustomAggregate, [CustomEventA])
    class CustomProjection(Projection):
        SnapshotClass = JsonSnapshot

    aagregate = CustomAggregate(auto_snapshot_each_n=2) # each two events, snapshots will be created
    event_a = CustomEventA()
    event_b = CustomEventB()

    aggregate.apply(event_a)
    aagregate.apply(event_b) # after that event, projection snapshot will be created, not only the Aggregate one

    storage = CustomEventStore()
    storage.save(aggregate) # snpahot is saved among with other events

    storage.load_projection(aggregate_id, CustomProjection) # projection will be loaded from snapshot
    storage.load_projection(aggregate_id, CustomProjection, from_snapshots=False) # projection will be loaded without snapshot


Define the Custom Snapshot
****************************************************************

.. code-block:: python

    from pyeventor.event import Snapshot
    class CustomSnapshot(Snapshot):

        @classmethod
        def create(cls, aggregate):
            data = ...# creating the data from aggregate somehow
            return cls(data=data)

    class CustomAggregate(Aggregate[int]):
        SnapshotClass = CustomSnapshot

        @classmethod
        def from_snapshot(
            cls, aggregate_id: int, snapshot: CustomSnapshot
        ) -> "Aggregate":
            obj = cls(aggregate_id)
            # fill object with attributes from snapshot
            return obj

