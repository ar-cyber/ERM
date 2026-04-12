import discord
from discord.ext import commands
import aiohttp
import logging

class Bloxlink:
    def __init__(self, bot: commands.Bot, key: str, rov_api_key):
        print(key)
        self.api_key = key
        self.blox_session = aiohttp.ClientSession(headers={"Authorization": self.api_key})
        self.rover_session = aiohttp.ClientSession(headers={"Authorization": f"Bearer {rov_api_key}"})
        bot.external_http_sessions.append(self.blox_session)
        bot.external_http_sessions.append(self.rover_session)
        self.bot = bot


    async def find_roblox(self, user_id: int, guild_id: int | None = None):
        doc = await self.bot.oauth2_users.db.find_one({"discord_id": user_id})
        if doc:
            return {"robloxID": doc["roblox_id"]}

        
        resp_json = await self.bot.redis.cache_bloxlink(session=self.blox_session, mode="discord", id=user_id, guild=guild_id)
        if resp_json:
            return resp_json
        
        resp_json = await self.bot.redis.cache_rover(session=self.rover_session, mode="discord", id=user_id, guild=guild_id)
    
    async def find_discord(self, user_id: int, guild_id: int):
        doc = None # await self.bot.oauth2_users.db.find_one({"roblox_id": user_id})
        if doc:
            return doc
        
        resp_json = await self.bot.redis.cache_bloxlink(session=self.blox_session, mode="roblox", id=user_id, guild=guild_id)
        if resp_json:
            return resp_json
        
        resp_json = await self.bot.redis.cache_rover(session=self.rover_session, mode="roblox", id=user_id, guild=guild_id)
        return resp_json
    async def get_roblox_info(self, user_id: int):
        if not user_id:
            return {}
        return await self.bot.redis.cache_get_roblox(user_id)
        
