from pyeventor.aggregate import Aggregate, Projection
from pyeventor.event import Event, Snapshot
from pyeventor.decorator import register_handler, projection


class UserData:
    def __init__(self, user_id, name, email, password):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password


# Define an event
class UserRegisteredEvent(Event[int, UserData]):
    ...


# Define an aggregate
class UserAggregate(Aggregate[str]):
    def _init_empty_attributes(self):
        self.user_id = None
        self.email = None
        self.name = None
        self.password = None

    @register_handler(UserRegisteredEvent)
    def user_registration(self, event: UserRegisteredEvent):
        self.user_id = event.data.user_id
        self.email = event.data.email
        self.name = event.data.name
        self.password = event.data.password


class UserChangeNameEvent(Event[int, UserData]):
    @register_handler(UserAggregate)
    def change_name(self, user: UserAggregate):
        user.name = self.data.name


user = UserAggregate()
registration_event = UserRegisteredEvent(
    data=UserData(
        user_id="1", name="John Doe", email="some@example.com", password="password"
    )
)
user.apply(registration_event)
