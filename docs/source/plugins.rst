Plugins
================================================================

In memory synchronous storage for events
****************************************************************

In memory storage implementation save events in a dict
It can be used as example of simple storage implementation.
It has no peristent storage

Example of usage

.. code-block:: python
    
    from pyeventor.plugins.in_memory_store import InMemoryEventStore
    class CustomInMemoryEventStore(InMemoryEventStore[CustomAggregate, int, str]):
        _AggregatedClass = CustomAggregate

    storage = CustomInMemoryEventStore()

For more information, see the :ref:`Examples`

Async postgres storage for events
****************************************************************

this storage work with the postgres and sqlalchemy to provide a complex example of event store creation.
It use two tables to store the data. One for events and one for Snapshots.
They are not created automatically, so it's possible to include them in alembic or any other db version control

Example of usage

.. code-block:: python
    
    from pyeventor.plugins.postgres_store import PostgresAsyncEventStore
    class CustomInMemoryEventStore(PostgresAsyncEventStore[CustomAsyncAggregate, int, str]):
        _AggregatedClass = CustomAsyncAggregate

    storage = CustomInMemoryEventStore()

For more information, see the :ref:`Examples`
