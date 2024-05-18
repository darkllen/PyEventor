Projection
================================================================

``Projection`` is used to provide a specific information about the ``Aggregate``, using only some of the events

It is immutable and new events can't be applied to it

Define the Projection
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

        @register_handler(CustomEventB)
        def custom_handler(self, event: CustomEventB):
            ...

        @register_handler(CustomEventA)
        def special_custom_handler(self, event: CustomEventA):
            ...

    @projection(CustomAggregate, [CustomEventA])
    class CustomProjection(Projection):

        def _init_empty_attributes(self):
            ...

        @register_handler(CustomEventA) 
        def redefine_apply(self, event: CustomEventA):
            # in case of absence of redefined, 
            # CustomAggregate will be used for resolving the handling
    
CustomProjection can work with all events that are defined in the projection decarator.
The handlers will be copied from the CustomAggregate (or it bases according the handling resolving)
Or they can be defined in the projection to change the befaviout


Usage of projection
********************************

.. code-block:: python
    
    storage = CustomEventStore()
    projection storage.load_projection(aggregate_id, CustomProjection)

With this we will gather and apply only certain events, not all of them 