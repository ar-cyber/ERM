import discord, datetime, asyncio, pytz
from utils.constants import BLANK_COLOR, GREEN_COLOR
class RiskyUsersMenu(discord.ui.View):
    def __init__(self, bot, guild_id, risky_users, user_id):
        super().__init__(timeout=600.0)
        self.bot = bot
        self.guild_id = guild_id
        self.risky_users = risky_users
        self.user_id = user_id
        self.add_item(BanOptions(bot, guild_id, risky_users, user_id))


class BanOptions(discord.ui.Select):
    def __init__(self, bot, guild_id, risky_users, user_id):
        self.bot = bot
        self.guild_id = guild_id
        self.risky_users = risky_users
        self.user_id = user_id
        options = [
            discord.SelectOption(label="Ban All Risk Users", description="Ban all detected risk users"),
            discord.SelectOption(label="Ban Specific User", description="Specify a user to ban")
        ]
        super().__init__(placeholder="Actions", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        await interaction.response.defer()
        self.view.clear_items()

        if self.values[0] == "Ban All Risk Users":
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{await self.bot.emoji_controller.get_emoji('Clock')} Banning users",
                    description="We are banning all the risk users in your server. Please wait...",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            for user in self.risky_users:
                ban_command = f":ban {user.id}"
                await self.bot.prc_api.run_command(self.guild_id, ban_command)
                await self.bot.punishments.insert_warning(
                    staff_id=int(interaction.user.id), # interaction id
                    staff_name= interaction.user.name, #interaction usr name
                    user_id=int(user.id),
                    user_name=user.username,
                    guild_id= interaction.guild.id,
                    moderation_type="Ban",
                    reason="Having a user with all or others.",
                    time_epoch= datetime.datetime.now(tz=pytz.UTC).timestamp(),
                )
                await asyncio.sleep(5)  # Rate limit: 1 command every 5 seconds
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{await self.bot.emoji_controller.get_emoji('success')} Players Banned",
                    description="All risk players have been banned from the server.",
                    color=GREEN_COLOR
                ), ephemeral=True
            )

        elif self.values[0] == "Ban Specific User":
            new_view = RiskyUsersMenu(self.bot, self.guild_id, self.risky_users, self.user_id)
            new_view.clear_items()
            new_view.add_item(SpecificUserSelect(self.bot, self.guild_id, self.risky_users, self.user_id))
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Select a User to Ban",
                    description="Please select a user from the dropdown below.",
                    color=BLANK_COLOR
                ), ephemeral=True, view=new_view
            )


class SpecificUserSelect(discord.ui.Select):
    def __init__(self, bot, guild_id, risky_users, user_id):
        self.bot = bot
        self.guild_id = guild_id
        self.risky_users = risky_users
        self.user_id = user_id
        options = [
            discord.SelectOption(label=user.username, value=str(user.id))
            for user in risky_users
        ]
        super().__init__(placeholder="Select a user to ban", options=options, max_values=len(options), min_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        await interaction.response.defer()
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{await self.bot.emoji_controller.get_emoji('Clock')} Banning users",
                description="We are banning the specified risk users in the server. Please wait...",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        for user_id in self.values:
            user_id = int(user_id)
            ban_command = f":ban {user_id}"
            await self.bot.prc_api.run_command(self.guild_id, ban_command)
            user = next((u for u in self.risky_users if u.id == user_id), None)
            if user:
                await self.bot.punishments.insert_warning(
                    staff_id=interaction.user.id,  # usr id
                    staff_name= interaction.user.name,  # interaction usr
                    user_id=int(user.id),
                    user_name=user.username,
                    guild_id=interaction.guild.id,
                    moderation_type="Ban",
                    reason="Having a user with all or others.",
                    time_epoch=datetime.datetime.now(tz=pytz.UTC).timestamp(),
                )
            await asyncio.sleep(5)  # Rate limit: 1 command every 5 seconds
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{await self.bot.emoji_controller.get_emoji('success')} Players Banned",
                description="The selected players have been banned from the server.",
                color=GREEN_COLOR
            ), ephemeral=True
        )
