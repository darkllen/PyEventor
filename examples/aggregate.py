from pyeventor.aggregate import Aggregate, Projection
from pyeventor.event import Event, JsonSnapshot
from pyeventor.decorator import register_handler, projection
import inspect


class UserData:
    def __init__(self, user_id, name, email, password):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password


# Define an event
class UserRegisteredEvent(Event[int, UserData]):
    ...


class UserSpendMoneyEvent(Event[int, int]):
    ...


class UserAskReceiptEvent(Event[int, None]):
    ...


# Define an aggregate
class UserAggregate(Aggregate[str]):
    def _init_empty_attributes(self):
        self.user_id = None
        self.email = None
        self.name = None
        self.password = None
        self.total_spending = 0

    @register_handler(UserRegisteredEvent)
    def user_registration(self, event: UserRegisteredEvent):
        self.user_id = event.data.user_id
        self.email = event.data.email
        self.name = event.data.name
        self.password = event.data.password

    @register_handler(UserSpendMoneyEvent)
    def user_spending(self, event: UserSpendMoneyEvent):
        self.total_spending += event.data

    @register_handler(UserAskReceiptEvent)
    def user_ask_receipt(self, event: UserAskReceiptEvent):
        print("some user receipt")


class UserChangeNameEvent(Event[int, str]):
    @register_handler(UserAggregate)
    def change_name(self, user: UserAggregate):
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
class MoneyOperationProjection(Projection):
    SnapshotClass = MoneyOperationProjectionSnapshot

    def _init_empty_attributes(self):
        self.total_spending = 0
        self.ask_receipt_times = 0

    @register_handler(UserAskReceiptEvent)
    def user_ask_receipt(self, event: UserAskReceiptEvent):
        self.ask_receipt_times += 1


if __name__ == "__main__":

    user = UserAggregate()
    registration_event = UserRegisteredEvent(
        data=UserData(
            user_id="1", name="John Doe", email="some@example.com", password="password"
        )
    )
    user.apply(registration_event)

    assert user.user_id == "1"
    assert user.name == "John Doe"
    assert user.password == "password"
    assert user.email == "some@example.com"

    change_name_event = UserChangeNameEvent(data="Other name")
    user.apply(change_name_event)
    assert user.user_id == "1"
    assert user.name == "Other name"
    assert user.password == "password"
    assert user.email == "some@example.com"

    projection = MoneyOperationProjection()

    spend_money_event = UserSpendMoneyEvent(10)
    ask_for_receipt_event = UserAskReceiptEvent()

    user.apply(spend_money_event)
    user.apply(ask_for_receipt_event)

    assert user.total_spending == 10

    projection.apply(spend_money_event)
    projection.apply(ask_for_receipt_event)

    assert projection.total_spending == 10
    assert projection.ask_receipt_times == 1

    # projection.apply(user_registration) -> error cause this projection can't work with such event

    snapshot = JsonSnapshot.create(user)
    assert snapshot.data == {
        "user_id": "1",
        "email": "some@example.com",
        "name": "Other name",
        "password": "password",
        "total_spending": 10,
    }

    user_from_snapshot = UserAggregate.from_snapshot(user.id, snapshot)

    assert user_from_snapshot.user_id == "1"
    assert user_from_snapshot.name == "Other name"
    assert user_from_snapshot.password == "password"
    assert user_from_snapshot.email == "some@example.com"
    assert user_from_snapshot.total_spending == 10

    projection_snapshot = MoneyOperationProjectionSnapshot.create(projection)

    assert projection_snapshot.data == {"total_spending": 10, "ask_receipt_times": 1}

    projection_from_snapshot = MoneyOperationProjection.from_snapshot(
        projection.id, projection_snapshot
    )

    assert projection_from_snapshot.total_spending == 10
    assert projection_from_snapshot.ask_receipt_times == 1
