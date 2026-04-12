"""
Redis file for ERM in order to avoid the stupid Roblox ratelimits.
This is an alternative to the hard caching used for other components. In this case, it is more efficient to use a redis database as it is persistent.
This is an NOT-OPTIONAL component of ERM and is required to be set up
"""

import redis.asyncio as redis
from aiohttp import ClientSession
from discord.ext import commands
import json
import typing
import inspect
from functools import wraps
import logging as l
logging = l.getLogger(__name__)

def redis_cache(key_template: str, ttl: int = 300):
        def decorator(func):
            sig = inspect.signature(func)
            @wraps(func)
            async def inner(*args, **kwargs):
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                data = bound.arguments
                try:
                    key = key_template.format(**data)
                except KeyError as e:
                    raise ValueError(f"Missing key field for cache key: {e}")
                redis_client = data.get("self").redis
                try:
                    cached = await redis_client.get(key)
                    if cached is not None:
                        logging.info(f"Loading cached data for {key}")
                        return json.loads(cached)
                except Exception:
                    pass

                result = await func(*args, **kwargs)

                try:
                    await redis_client.set(key, json.dumps(result), ex=ttl)
                except Exception:
                    pass

                return result

            return inner
        return decorator

class ERMRedis:
    def __init__(self, bot: commands.Bot, connection: redis.Redis):
        self.bot = bot
        self.redis = connection

    
    # Cache Roblox response
    @redis_cache("roblox:{user_id}")
    async def cache_get_roblox(self, user_id):
        async with ClientSession() as sess:
            return await (await sess.get(f"https://users.roblox.com/v1/users/{user_id}")).json()
        
    @redis_cache("bloxlink:{mode}:{id}", ttl=300)
    async def cache_bloxlink(self, mode: typing.Literal["discord", "roblox"], id: int, session: ClientSession, guild: int=None):
        if mode == "roblox" and guild == None:
            raise Exception("Roblox lookup is guild only. A guild id must be specified")
        match mode:
            case "discord":
                if guild is not None:
                    data = await session.get(f"https://api.blox.link/v4/public/guilds/{guild}/discord-to-roblox/{id}")
                    json = await data.json()
                    if data.status == 404 or json.get("robloxID", "") == "":
                        return json
                else:
                    data = await session.get(f"https://api.blox.link/v4/public/discord-to-roblox/{id}")
                    json = await data.json()
                    if data.status == 404 or json.get("robloxID", "") == "":
                        return {}
                print(json)
                return self.cache_get_roblox(int(json["robloxID"]))
            case "roblox":
                data = await session.get(f"https://api.blox.link/v4/public/guilds/{guild}/roblox-to-discord/{id}")
                json = await data.json()
                print(json)
                if json.get("discordIDs", []) == []:
                    return {}
                return json["discordIDs"][0]
            case _:
                raise Exception("Invalid mode specified. Must be one of: 'discord', 'roblox'.")

        
    @redis_cache("rover:{mode}:{id}:{guild}", ttl=600)
    async def cache_rover(self, mode: typing.Literal["discord", "roblox"], id: int, session: ClientSession, guild: int):
        match mode:
            case "discord":
                data = await session.get(f"https://registry.rover.link/api/guilds/{guild}/discord-to-roblox/{id}")
                json = await data.json()
                if data.status == 404 or json.get("robloxId", "") == "":
                    return {}
                return self.cache_get_roblox(int(json["robloxId"]))
            case "roblox":
                data = await session.get(f"https://registry.rover.link/api/guilds/{guild}/roblox-to-discord/{id}")
                json = await data.json()
                print(json)
                if json.get("discordUsers", []) == []:
                    return {}
                return json["discordUsers"]
            case _:
                raise Exception("Invalid mode specified. Must be one of: 'discord', 'roblox'.")
