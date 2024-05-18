Asyncio
================================================================

Async is provided with separate async interfaces

Defining the asyncio implementation
****************************************************************

.. code-block:: python
    
    from pyeventor.asyncio.aggregate import AsyncAggregate, AsyncProjection
    from pyeventor.event import Event 
    from pyeventor.decorator import register_handler, projection
    from pyeventor.asyncio.event_store import (
        AsyncEventStore,
        IdTypeHint,
        SequenceHint,
        AggregateAsyncHint,
    )
    
    class CustomEventA(Event[int, None]):
        ...
    class CustomAggregate(AsyncAggregate[str]):

        @register_handler(CustomEventA)
        async def user_registration(self, event: CustomEventA):
            ...

    @projection(CustomAggregate, [CustomEventA])
    class CustomProjection(AsyncProjection):

        @register_handler(CustomEventA) 
        async def redefine_apply(self, event: CustomEventA):
            ...

    class CustomEventStore(EventStore[AggregateAsyncHint, SequenceHint, IdTypeHint]):
        ...
        # all the methods are async 

So, as async should be defiend:
    * all the handlers
    * all the methods of the event store