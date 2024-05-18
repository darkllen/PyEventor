from pyeventor.plugins.in_memory_store import InMemoryEventStore
from examples.aggregate import (
    UserAggregate,
    UserRegisteredEvent,
    UserSpendMoneyEvent,
    UserAskReceiptEvent,
    MoneyOperationProjection,
    UserData,
    JsonSnapshot,
    MoneyOperationProjectionSnapshot,
)
from time import sleep
from datetime import datetime


class UserInMemoryEventStore(InMemoryEventStore[UserAggregate, int, str]):
    _AggregatedClass = UserAggregate


if __name__ == "__main__":

    user_storage = UserInMemoryEventStore()

    user = UserAggregate()
    registration_event = UserRegisteredEvent(
        data=UserData(
            user_id="1", name="John Doe", email="some@example.com", password="password"
        )
    )
    user.apply(registration_event)

    user_storage.save(user)

    loaded_user = user_storage.load(user)

    assert user.name == "John Doe"
    assert user.user_id == "1"
    assert user.password == "password"
    assert user.email == "some@example.com"

    time_for_load_at = datetime.now()
    sleep(1)

    spend_money_event = UserSpendMoneyEvent(10)
    ask_for_receipt_event = UserAskReceiptEvent()

    user.apply(spend_money_event)
    user.apply(ask_for_receipt_event)

    user_storage.save(user)

    projection = user_storage.load_projection(user.id, MoneyOperationProjection)

    assert projection.total_spending == 10
    assert projection.ask_receipt_times == 1

    part_user = user_storage.load(user.id, load_at=time_for_load_at)
    assert part_user.total_spending == 0

    user_with_snapshots = UserAggregate(auto_snapshot_each_n=2)

    user_with_snapshots.apply(registration_event)
    user_with_snapshots.apply(spend_money_event)
    user_with_snapshots.apply(ask_for_receipt_event)

    assert isinstance(
        user_with_snapshots.uncommmited_events[-2], MoneyOperationProjectionSnapshot
    )
    assert isinstance(user_with_snapshots.uncommmited_events[-3], JsonSnapshot)

    user_storage.save(user_with_snapshots)

    user_loaded_from_snpahot = user_storage.load(user.id)

    assert user_loaded_from_snpahot.name == "John Doe"
    assert user_loaded_from_snpahot.user_id == "1"
    assert user_loaded_from_snpahot.password == "password"
    assert user_loaded_from_snpahot.email == "some@example.com"
    assert user_loaded_from_snpahot.total_spending == 10

    projection_loaded_from_snpahot = user_storage.load_projection(
        user.id, MoneyOperationProjection
    )

    assert projection_loaded_from_snpahot.total_spending == 10
    assert projection_loaded_from_snpahot.ask_receipt_times == 1
