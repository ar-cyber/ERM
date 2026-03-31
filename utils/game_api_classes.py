from .basedataclass import BaseDataClass
import typing
from discord.ext import commands

class ResponseFailure(Exception):
    detail: str | None
    status_code: int
    json_data: dict

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"{self.status_code}: {self.json_data}"



class BanItem(BaseDataClass):
    username: str
    user_id: int


class CommandLog(BaseDataClass):
    username: str
    user_id: int
    timestamp: int
    is_automated: bool
    command: str


class JoinLeaveLog(BaseDataClass):
    type: typing.Literal["join", "leave"]
    timestamp: int
    username: str
    user_id: int

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class KillLog(BaseDataClass):
    killer_username: str
    killer_user_id: int
    timestamp: int
    killed_username: str
    killed_user_id: int

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class Player(BaseDataClass):
    username: str
    id: int
    permission: typing.Optional[
        typing.Literal[
            "Server Administrator",
            "Server Moderator",
            "Normal",
            "Server Owner",
            "Server Co-Owner",
        ]
    ] = None  # This doesn't return when we query for queue, so we type for optional.
    callsign: str | None = None
    team: str | None = None


class ModCall(BaseDataClass):
    caller: str
    moderator: str | None = None
    timestamp: int


class ServerStatus(BaseDataClass):
    name: str
    owner_id: int
    co_owner_ids: list[int]
    current_players: int
    max_players: int
    join_key: str
    account_verified_request: bool
    team_balance: bool


class ActiveVehicle(BaseDataClass):
    username: str
    texture: str
    vehicle: str


class ServerLinkNotFound(commands.CheckFailure):
    def __init__(self, platform: typing.Optional[str]):
        self.platform = platform
        super().__init__()

    platform: str = "erlc"
    code: int = 0
