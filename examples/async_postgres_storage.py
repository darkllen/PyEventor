from pyeventor.asyncio.aggregate import AsyncAggregate, AsyncProjection
from pyeventor.event import Event, JsonSnapshot
from pyeventor.decorator import register_handler, projection
import inspect
from pyeventor.plugins.postgres_store import PostgresAsyncEventStore
import os
from datetime import datetime
from time import sleep
import asyncio


class UserData(dict):
    def __init__(self, user_id, name, email, password):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password

        dict.__init__(
            self,
            user_id=self.user_id,
            name=self.name,
            email=self.email,
            password=self.password,
        )


# Define an event
class UserRegisteredEvent(Event[int, UserData]):
    ...


class UserSpendMoneyEvent(Event[int, dict]):
    ...


class UserAskReceiptEvent(Event[int, dict]):
    ...


# Define an aggregate
class UserAggregate(AsyncAggregate[str]):
    def _init_empty_attributes(self):
        self.user_id = None
        self.email = None
        self.name = None
        self.password = None
        self.total_spending = 0

    @register_handler(UserRegisteredEvent)
    async def user_registration(self, event: UserRegisteredEvent):
        self.user_id = event.data.user_id
        self.email = event.data.email
        self.name = event.data.name
        self.password = event.data.password

    @register_handler(UserSpendMoneyEvent)
    async def user_spending(self, event: UserSpendMoneyEvent):
        self.total_spending += event.data["amount"]

    @register_handler(UserAskReceiptEvent)
    async def user_ask_receipt(self, event: UserAskReceiptEvent):
        print("some user receipt")


class UserChangeNameEvent(Event[int, str]):
    @register_handler(UserAggregate)
    async def change_name(self, user: UserAggregate):
        user.name = self.data


class MoneyOperationProjectionSnapshot(JsonSnapshot):
    @classmethod
    def create(cls, aggregate):
        attributes = {
            k: v
            for k, v in aggregate.__dict__.items()
            if not k.startswith("_") and not inspect.ismethod(getattr(aggregate, k))
        }
        print("some additional action")
        return MoneyOperationProjectionSnapshot(data=attributes)


@projection(UserAggregate, [UserSpendMoneyEvent, UserAskReceiptEvent])
class MoneyOperationProjection(AsyncProjection):
    SnapshotClass = MoneyOperationProjectionSnapshot

    def _init_empty_attributes(self):
        self.total_spending = 0
        self.ask_receipt_times = 0

    @register_handler(UserAskReceiptEvent)
    async def user_ask_receipt(self, event: UserAskReceiptEvent):
        self.ask_receipt_times += 1


class UserAsyncEventStore(PostgresAsyncEventStore[UserAggregate, int, str]):
    _AggregatedClass = UserAggregate


async def main():
    db_url = os.environ.get("DB_URL", "postgresql+asyncpg://user:password@host:port/db")
    user_storage = UserAsyncEventStore(db_url)

    user = UserAggregate()
    registration_event = UserRegisteredEvent(
        data=UserData(
            user_id="1", name="John Doe", email="some@example.com", password="password"
        )
    )
    await user.apply(registration_event)

    await user_storage.save(user)

    loaded_user = await user_storage.load(user.id)

    assert loaded_user.name == "John Doe"
    assert loaded_user.user_id == "1"
    assert loaded_user.password == "password"
    assert loaded_user.email == "some@example.com"

    time_for_load_at = datetime.now()
    sleep(1)

    spend_money_event = UserSpendMoneyEvent({"amount": 10})
    ask_for_receipt_event = UserAskReceiptEvent({})

    await user.apply(spend_money_event)
    await user.apply(ask_for_receipt_event)

    await user_storage.save(user)

    projection = await user_storage.load_projection(user.id, MoneyOperationProjection)

    assert projection.total_spending == 10
    assert projection.ask_receipt_times == 1

    part_user = await user_storage.load(user.id, load_at=time_for_load_at)
    assert part_user.total_spending == 0

    user_with_snapshots = UserAggregate(auto_snapshot_each_n=2)

    await user_with_snapshots.apply(registration_event)
    await user_with_snapshots.apply(spend_money_event)
    await user_with_snapshots.apply(ask_for_receipt_event)

    assert isinstance(
        user_with_snapshots.uncommmited_events[-2], MoneyOperationProjectionSnapshot
    )
    assert isinstance(user_with_snapshots.uncommmited_events[-3], JsonSnapshot)

    await user_storage.save(user_with_snapshots)

    user_loaded_from_snpahot = await user_storage.load(user.id)

    assert user_loaded_from_snpahot.name == "John Doe"
    assert user_loaded_from_snpahot.user_id == "1"
    assert user_loaded_from_snpahot.password == "password"
    assert user_loaded_from_snpahot.email == "some@example.com"
    assert user_loaded_from_snpahot.total_spending == 10

    projection_loaded_from_snpahot = await user_storage.load_projection(
        user.id, MoneyOperationProjection
    )

    assert projection_loaded_from_snpahot.total_spending == 10
    assert projection_loaded_from_snpahot.ask_receipt_times == 1


if __name__ == "__main__":
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(main())
