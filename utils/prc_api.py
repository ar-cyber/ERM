import asyncio
import datetime
import typing

import discord
import roblox
from discord.ext import commands
import aiohttp
from utils.basedataclass import BaseDataClass
from datamodels.ServerKeys import ServerKey

from game_api_classes import *


class PRCApiClient:
    def __init__(self, bot, base_url: str, api_key: str):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.api_key = api_key
        self.base_url = base_url

        bot.external_http_sessions.append(self.session)

    async def get_server_key(self, guild_id: int) -> ServerKey:
        return await self.bot.server_keys.get_server_key(
            guild_id
        ) 

    async def _send_api_request(
        self,
        method: typing.Literal["GET", "POST"],
        endpoint: str,
        guild_id: int,
        data: dict | None = None,
        key: str | None = None,
        max_retries: int = 2,
    ):

        global_key = self.api_key
        use_global_key = bool(global_key)
        if not key:
            internal_server_object = await self.get_server_key(guild_id)
            internal_server_key = (
                internal_server_object if internal_server_object is not None else None
            )
            if internal_server_key is None:
                return 401, {}
            else:
                internal_server_key = internal_server_key.key
        else:
            internal_server_key = key

        headers = (
            {"Authorization": global_key, "Server-Key": internal_server_key}
            if use_global_key
            else {"Server-Key": internal_server_key}
        )

        async with self.session.request(
            method,
            url=f"{self.base_url}{endpoint}",
            headers=headers,
            json=data or {},
        ) as response:
            # if response.status == 403:
            #     await self.bot.prohibited.insert({
            #         "_id": ObjectId(),
            #         "ServerKey": internal_server_key,
            #         "ProhibitedUntil": 9999999999
            #     })
            if response.status in {429, 502}:
                if max_retries <= 0:
                    raise ResponseFailure(
                        status_code=response.status,
                        json_data={"error": "Max retries exceeded"},
                    )
                retry_after = int((await response.json()).get("retry_after", 5)) if response.status == 429 else 5
                await asyncio.sleep(retry_after)
                return await self._send_api_request(
                    method=method,
                    endpoint=endpoint,
                    guild_id=guild_id,
                    data=data,
                    key=key,
                    max_retries=max_retries - 1,
                )
            return response.status, (
                await response.json() if response.content_type != "text/html" else {}
            )

    async def get_server_status(self, guild_id: int):
        status_code, response_json = await self._send_api_request(
            "GET", "/server", guild_id
        )
        if status_code == 200:
            return ServerStatus(
                name=response_json["Name"],
                owner_id=response_json["OwnerId"],
                co_owner_ids=response_json["CoOwnerIds"],
                current_players=response_json["CurrentPlayers"],
                max_players=response_json["MaxPlayers"],
                join_key=response_json["JoinKey"],
                account_verified_request=response_json["AccVerifiedReq"] == "Enabled",
                team_balance=response_json["TeamBalance"],
            )
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def send_test_request(self, server_key: str) -> int | ServerStatus:
        code, response_json = await self._send_api_request(
            "GET", "/server", 0, None, server_key
        )
        return (
            code
            if code != 200
            else ServerStatus(
                name=response_json["Name"],
                owner_id=response_json["OwnerId"],
                co_owner_ids=response_json["CoOwnerIds"],
                current_players=response_json["CurrentPlayers"],
                max_players=response_json["MaxPlayers"],
                join_key=response_json["JoinKey"],
                account_verified_request=response_json["AccVerifiedReq"] == "Enabled",
                team_balance=response_json["TeamBalance"],
            )
        )

    async def get_server_players(self, guild_id: int) -> list:
        status_code, response_json = await self._send_api_request(
            "GET", "/server/players", guild_id
        )
        if status_code == 200:
            new_list = []
            for item in response_json:
                new_list.append(
                    Player(
                        username=item["Player"].split(":")[0],
                        id=item["Player"].split(":")[1],
                        permission=item["Permission"],
                        callsign=item.get("Callsign"),
                        team=item["Team"],
                    )
                )
            return new_list
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def get_mod_calls(self, guild_id: int) -> list:
        status_code, response_json = await self._send_api_request(
            "GET", "/server/modcalls", guild_id
        )
        if status_code == 200:
            return [
                ModCall(
                    caller_username=call["Caller"].split(":")[0],
                    caller_id=call["Caller"].split(":")[1],
                    moderator_username=call.get("Moderator").split(":")[0] if call.get("Moderator") else None,
                    moderator_id=call.get("Moderator").split(":")[1] if call.get("Moderator") else None,
                    timestamp=call["Timestamp"],
                )
                for call in response_json
            ]
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def get_server_staff(self, guild_id: int) -> list:
        status_code, response_json = await self._send_api_request(
            "GET", "/server/staff", guild_id
        )
        if status_code == 200:
            co_owners = response_json.get("CoOwners", [])
            roblox_client = roblox.Client()
            co_owner_users = await roblox_client.get_users(co_owners, expand=False)
            co_owner_names = [user.name for user in co_owner_users]
            co_owners = dict(zip(co_owners, co_owner_names))
            try:
                players = [Player(username=v, id=k, permission="Server Co-Owner") for k,v in co_owners.items()]
            except AttributeError:
                players = []
            try:
                players += [Player(
                    username=v, id=k, permission="Server Administrator"
                ) for k,v in response_json.get("Admins", {}).items()]
            except AttributeError:
                players += []
            try:
                players += [Player(
                    username=v, id=k, permission="Server Moderator"
                ) for k,v in response_json.get("Mods", {}).items()]
            except:
                players += []
            return players
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def get_server_vehicles(self, guild_id: int) -> list:
        status_code, response_json = await self._send_api_request(
            "GET", "/server/vehicles", guild_id
        )
        if status_code == 200:
            return [
                ActiveVehicle(
                    texture=i.get("Texture", "Default"),
                    username=i["Owner"],
                    vehicle=i["Name"],
                )
                for i in response_json
            ]
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def get_server_queue(self, guild_id: int, minimal: bool = False) -> list:
        status_code, response_json = await self._send_api_request(
            "GET", "/server/queue", guild_id
        )
        if status_code == 200:
            if minimal:
                return len(response_json)
            new_list = []
            for user in await self.bot.roblox.get_users(response_json, expand=False):
                new_list.append(Player(username=user.name, id=user.id))
            return new_list
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def fetch_server_logs(self, guild_id: int):
        status_code, response_json = await self._send_api_request(
            "GET", "/server/commandlogs", guild_id
        )
        if status_code == 200:
            return [
                CommandLog(
                    username=(
                        log_item["Player"].split(":")[0]
                        if ":" in log_item["Player"]
                        else log_item["Player"]
                    ),
                    user_id=(
                        log_item["Player"].split(":")[1]
                        if ":" in log_item["Player"]
                        else 0
                    ),
                    timestamp=log_item["Timestamp"],
                    is_automated=log_item["Player"] == "Remote Server",
                    command=log_item["Command"],
                )
                for log_item in response_json
            ]
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def fetch_kill_logs(self, guild_id: int):
        status_code, response_json = await self._send_api_request(
            "GET", "/server/killlogs", guild_id
        )
        if status_code == 200:
            return [
                KillLog(
                    killer_username=log_item["Killer"].split(":")[0],
                    killer_user_id=log_item["Killer"].split(":")[1],
                    timestamp=log_item["Timestamp"],
                    killed_username=log_item["Killed"].split(":")[0],
                    killed_user_id=log_item["Killed"].split(":")[1],
                )
                for log_item in response_json
            ]
        elif status_code == 429:
            retry_after = int(response_json.get("retry_after", 5))
            await asyncio.sleep(retry_after)
            return await self.fetch_kill_logs(guild_id)
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def fetch_bans(self, guild_id: int):
        status_code, response_json = await self._send_api_request(
            "GET", "/server/bans", guild_id
        )

        if status_code == 200:
            if response_json == []:
                return []
            return [
                BanItem(
                    user_id=int(user_id) if user_id.isdigit() else 0, username=username
                )
                for user_id, username in response_json.items()
            ]
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def fetch_player_logs(self, guild_id: int):
        status_code, response_json = await self._send_api_request(
            "GET", "/server/joinlogs", guild_id
        )
        if status_code == 200:
            return [
                JoinLeaveLog(
                    username=log_item["Player"].split(":")[0],
                    user_id=log_item["Player"].split(":")[1],
                    timestamp=log_item["Timestamp"],
                    type="join" if log_item["Join"] is True else "leave",
                )
                for log_item in response_json
            ]
        elif status_code == 429:
            retry_after = int(response_json.get("retry_after", 5))
            await asyncio.sleep(retry_after)
            return await self.fetch_player_logs(guild_id)
        else:
            raise ResponseFailure(status_code=status_code, json_data=response_json)

    async def run_command(self, guild_id: int, command: str):
        status_code, response_json = await self._send_api_request(
            "POST", "/server/command", guild_id, data={"command": command}
        )
        if status_code == 429:
            await asyncio.sleep(response_json["retry_after"] + 0.1)
            return await self.run_command(guild_id, command)
        return status_code, response_json

    async def unban_user(self, guild_id: int, user_id: int):
        status_code = 0
        while status_code != 200:
            status_code, response_json = await self._send_api_request(
                "POST",
                "/server/command",
                guild_id,
                data={"command": ":unban {}".format(str(user_id))},
            )
            if status_code == 429:
                await asyncio.sleep(response_json["retry_after"] + 0.1)
            else:
                return status_code

