import discord
from utils.utils import config_change_log
from utils.constants import RED_COLOR, GREEN_COLOR
from .custommodal import CustomModal

class CreateERLCStats(discord.ui.View):
    def __init__(self, bot, user_id, guild_id):
        super().__init__(timeout=600.0)
        self.bot = bot
        self.value = None
        self.user_id = user_id
        self.limit = 1
        self.placeholder = "Select a channel"
        self.guild_id = guild_id

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.voice]
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Set Format", style=discord.ButtonStyle.secondary, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.ChannelSelect):
                select = child

        if interaction.user.id == self.user_id:
            self.value = select.values
            modal = CustomModal(
                "Format",
                [
                    (
                        "format",
                        discord.ui.TextInput(
                            label="Format",
                            placeholder=f"Format With Variables {', '.join([f'`{i}`' for i in ['onduty', 'join_code', 'players', 'etc']])}",
                        ),
                    )
                ],
            )
            await interaction.response.send_modal(modal)
            await modal.wait()
            if not modal.format.value:
                return
            channel_id = str(self.value[0].id)
            try:
                sett = await self.bot.settings.find_by_id(self.guild_id)
            except KeyError:
                sett = {}

            if "ERLC" not in sett:
                sett["ERLC"] = {"statistics": {}}
            elif "statistics" not in sett["ERLC"]:
                sett["ERLC"]["statistics"] = {}

            if channel_id in sett["ERLC"]["statistics"]:
                return await interaction.edit_original_response(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji_controller.get_emoji('error')} Error",
                        description=f"<#{channel_id}> is already set as a statistics channel",
                        color=discord.Color.red(),
                    ).set_author(
                        name=interaction.guild.name,
                        icon_url=(
                            interaction.guild.icon.url if interaction.guild.icon else ""
                        ),
                    ),
                    view=None,
                )

            sett["ERLC"]["statistics"][channel_id] = {"format": modal.format.value}

            await self.bot.settings.update_by_id(sett)
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"<#{channel_id}>: {modal.format.value}",
            )
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Success",
                    description=f"Statistics format for <#{channel_id}> has been set to `{modal.format.value}`",
                    color=discord.Color.green(),
                ),
                view=None,
            )


class EditERLCStats(discord.ui.View):
    def __init__(self, bot, user_id, guild_id):
        super().__init__(timeout=600.0)
        self.bot = bot
        self.value = None
        self.user_id = user_id
        self.limit = 1
        self.placeholder = "Select a channel"
        self.guild_id = guild_id

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.voice]
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Set Format", style=discord.ButtonStyle.secondary, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.ChannelSelect):
                select = child

        if interaction.user.id == self.user_id:
            self.value = select.values
            modal = CustomModal(
                "Format",
                [
                    (
                        "format",
                        discord.ui.TextInput(
                            label="Format",
                            placeholder=f"Format With Variables {', '.join([f'`{i}`' for i in ['onduty', 'join_code', 'players', 'etc']])}",
                        ),
                    )
                ],
            )
            await interaction.response.send_modal(modal)
            await modal.wait()
            if not modal.format.value:
                return
            channel_id = str(self.value[0].id)
            try:
                sett = await self.bot.settings.find_by_id(self.guild_id)
            except KeyError:
                sett = {}
            try:
                if channel_id not in sett["ERLC"]["statistics"]:
                    return await interaction.edit_original_response(
                        embed=discord.Embed(
                            title=f"{self.bot.emoji_controller.get_emoji('error')} Error",
                            description=f"<#{channel_id}> is not set as a statistics channel",
                            color=RED_COLOR,
                        ).set_author(
                            name=interaction.guild.name,
                            icon_url=(
                                interaction.guild.icon.url
                                if interaction.guild.icon
                                else ""
                            ),
                        ),
                        view=None,
                    )
            except KeyError:
                return await interaction.edit_original_response(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji_controller.get_emoji('error')} Error",
                        description=f"<#{channel_id}> is not set as a statistics channel",
                        color=RED_COLOR,
                    ).set_author(
                        name=interaction.guild.name,
                        icon_url=(
                            interaction.guild.icon.url if interaction.guild.icon else ""
                        ),
                    ),
                    view=None,
                )
            sett["ERLC"]["statistics"][channel_id]["format"] = modal.format.value
            await self.bot.settings.update_by_id(sett)
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"ER:LC Statistics Format for <#{channel_id}> has been set to `{modal.format.value}`",
            )
            msg = interaction.message.embeds[0]
            msg.title = f"<:check:1163142000271429662> Channel Updated"
            msg.description = (
                f"**Channel:** <#{channel_id}>\n> **Format:** `{modal.format.value}`"
            )
            await interaction.edit_original_response(embed=msg, view=None)


class DeleteERLCStats(discord.ui.View):
    def __init__(self, bot, user_id, guild_id, embed):
        super().__init__(timeout=600.0)
        self.bot = bot
        self.value = None
        self.user_id = user_id
        self.limit = 1
        self.placeholder = "Select a channel"
        self.guild_id = guild_id

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.voice]
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, row=2)
    async def remove_channel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        for child in self.children:
            if isinstance(child, discord.ui.ChannelSelect):
                select = child

        if interaction.user.id == self.user_id:
            self.value = select.values
            channel_id = self.value[0].id
            try:
                sett = await self.bot.settings.find_by_id(self.guild_id)
            except KeyError:
                sett = {}

            try:
                channel_id = str(channel_id)
                del sett["ERLC"]["statistics"][channel_id]
            except KeyError:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji_controller.get_emoji('error')} Error",
                        description=f"<#{channel_id}> is not set as a statistics channel",
                        color=RED_COLOR,
                    ).set_author(
                        name=interaction.guild.name,
                        icon_url=(
                            interaction.guild.icon.url if interaction.guild.icon else ""
                        ),
                    ),
                    view=None,
                    ephemeral=True,
                )
            await self.bot.settings.update_by_id(sett)
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"<#{channel_id}> Removed from ERLC Statistics",
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="<:success:1163149118366040106> Success",
                    description=f"<#{channel_id}> has been removed from ERLC Statistics",
                    color=GREEN_COLOR,
                ),
                view=None,
                ephemeral=True,
            )
