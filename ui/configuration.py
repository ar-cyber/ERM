# TODO: Refactor this mess at one point. It's better than before

import discord
from acv import AssociationConfigurationView
from utils.utils import config_change_log, time_converter, generator
from utils.timestamp import td_format
from utils.constants import BLANK_COLOR, GREEN_COLOR
import datetime
from custommodal import *
import roblox
from discord import Interaction
from erlcstatshelpers import *
from discord.ext import commands

# HELPERSs
class RoleQuotaManagement(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=600.0)
        self.user_id = user_id
        self.value = None
        self.selected_for_deletion = None
        self.name_for_creation = None
        self.modal = None

    @discord.ui.button(label="Create Role Quota")
    async def _create(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        await interaction.response.defer(thinking=False)
        self.value = "create"
        self.stop()

    @discord.ui.button(label="Delete Role Quota")
    async def _delete(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        self.modal = CustomModal(
            "Role Quota Deletion",
            [
                (
                    "role_id",
                    discord.ui.TextInput(label="Role ID", placeholder="ID of the Role"),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.role_id.value:
            self.selected_for_deletion = self.modal.role_id.value
        else:
            return
        self.value = "delete"
        self.stop()


class ShiftTypeManagement(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=600.0)
        self.user_id = user_id
        self.value = None
        self.selected_for_deletion = None
        self.name_for_creation = None
        self.modal = None

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def _create(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        # await interaction.response.defer(thinking=False)
        self.modal = CustomModal(
            "Create Shift Type",
            [
                (
                    "shift_type_name",
                    discord.ui.TextInput(
                        label="Name", placeholder="Name of Shift Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.shift_type_name.value:
            self.name_for_creation = self.modal.shift_type_name.value
        else:
            return
        self.value = "create"
        self.stop()

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def _edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        # await interaction.response.defer(thinking=False)
        self.modal = CustomModal(
            "Edit Shift Type",
            [
                (
                    "shift_type_name",
                    discord.ui.TextInput(
                        label="Name", placeholder="Name of Shift Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.shift_type_name.value:
            self.name_for_creation = self.modal.shift_type_name.value
        else:
            return
        self.value = "edit"
        self.stop()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def _delete(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        self.modal = CustomModal(
            "Shift Type Deletion",
            [
                (
                    "shift_type",
                    discord.ui.TextInput(
                        label="Shift Type ID", placeholder="ID of the Shift Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.shift_type.value:
            self.selected_for_deletion = self.modal.shift_type.value
        else:
            return
        self.value = "delete"
        self.stop()


class AutomaticShiftConfiguration(discord.ui.View):
    def __init__(
        self,
        bot,
        sustained_interaction: Interaction,
        shift_types: list,
        auto_data: dict,
    ):
        self.bot = bot
        self.shift_types = shift_types
        self.sustained_interaction = sustained_interaction
        self.auto_data = auto_data
        super().__init__(timeout=None)
        self.toggle_button_styling()

    def toggle_button_styling(self):
        for item in self.children:
            if item.label == "Change Shift Type":
                item.disabled = (
                    True
                    if (
                        len(self.shift_types) == 0
                        and self.auto_data.get("shift_type") == "Default"
                    )
                    else False
                )

    @discord.ui.button(
        label="Toggle Automatic Shifts", style=discord.ButtonStyle.secondary
    )
    async def toggle_automatic_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.auto_data["enabled"] = not self.auto_data["enabled"]
        self.toggle_button_styling()
        embed = discord.Embed(
            title="Automatic Shifts", description="", color=BLANK_COLOR
        )
        for key, value in self.auto_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {(value or 'Default') if isinstance(value, str) else ('<:check:1163142000271429662>' if value is True else '<:xmark:1166139967920164915>')}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        await (await self.sustained_interaction.original_response()).edit(
            embed=embed, view=self
        )
        await interaction.response.defer(thinking=False)

    @discord.ui.button(
        label="Change Shift Type",
        style=discord.ButtonStyle.secondary,
        row=1,
        disabled=True,
    )
    async def change_shift_type(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            modal := CustomModal(
                "Change Shift Type",
                [("shift_type", discord.ui.TextInput(label="Shift Type"))],
                {"ephemeral": True},
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        if not modal.shift_type.value:
            return

        if modal.shift_type.value.lower() == "default":
            self.auto_data["shift_type"] = "Default"
        else:
            if (
                selected := {i["name"].lower(): i for i in self.shift_types}.get(
                    modal.shift_type.value.lower()
                )
            ) is None:
                return await modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="This Shift Type does not exist in your server.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
            self.auto_data["shift_type"] = selected["name"]

        self.toggle_button_styling()
        embed = discord.Embed(
            title="Automatic Shifts", description="", color=BLANK_COLOR
        )
        for key, value in self.auto_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {(value or 'Default') if isinstance(value, str) else ('<:check:1163142000271429662>' if value is True else '<:xmark:1166139967920164915>')}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        await (await self.sustained_interaction.original_response()).edit(
            embed=embed, view=self
        )
        # await interaction.response.defer(thinking=False)

    @discord.ui.button(
        label="Finish Configuration", style=discord.ButtonStyle.success, row=2
    )
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await (await self.sustained_interaction.original_response()).delete()
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        if not sett:
            return
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["automatic_shifts"] = self.auto_data
        await self.bot.settings.update_by_id(sett)


class RemoteCommandConfiguration(discord.ui.View):
    def __init__(
        self,
        bot,
        sustained_interaction: Interaction,
        shift_types: list,
        auto_data: dict,
    ):
        self.bot = bot
        self.shift_types = shift_types
        self.sustained_interaction = sustained_interaction
        self.auto_data = auto_data
        super().__init__(timeout=None)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Webhook Channel",
        max_values=1,
        min_values=0,
    )
    async def webhook_channel(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        if len(select.values) == 0:
            self.auto_data["webhook_channel"] = None
        else:
            self.auto_data["webhook_channel"] = select.values[0].id
        print(self.auto_data)
        embed = discord.Embed(
            title="Remote Commands", description="", color=BLANK_COLOR
        )
        for key, value in self.auto_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {'<#' + str(value) + '>' if isinstance(value, int) else 'None'}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        await (await self.sustained_interaction.original_response()).edit(
            embed=embed, view=self
        )
        await interaction.response.defer(thinking=False)

    @discord.ui.button(
        label="Finish Configuration", style=discord.ButtonStyle.success, row=2
    )
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await (await self.sustained_interaction.original_response()).delete()
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        if not sett:
            return
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["remote_commands"] = self.auto_data
        await self.bot.settings.update_by_id(sett)


class WelcomeMessagingConfiguration(discord.ui.View):
    def __init__(self, bot, sustained_interaction: Interaction, welcome_message: str):
        self.bot = bot
        self.sustained_interaction = sustained_interaction
        self.welcome_message = welcome_message
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Set Welcome Message",
    )
    async def webhook_channel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = CustomModal(
            f"Set Welcome Message",
            [
                (
                    "welcome_message",
                    (
                        discord.ui.TextInput(
                            label="Welcome Message",
                            placeholder="Enter a welcome message to appear to players in your server.",
                            required=True,
                        )
                    ),
                )
            ],
        )
        await interaction.response.send_modal(modal)

        timeout = await modal.wait()
        if timeout:
            return

        welcome_message = modal.welcome_message.value

        embed = discord.Embed(
            title="Welcome Messaging",
            description="*This module allows for a message to appear to players of your server when they initially join your server.*\n\n",
            color=BLANK_COLOR,
        )
        embed.description += f"**Welcome Message:** {welcome_message if welcome_message != '' else 'None'}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        self.welcome_message = welcome_message
        await (await self.sustained_interaction.original_response()).edit(
            embed=embed, view=self
        )

    @discord.ui.button(
        label="Finish Configuration", style=discord.ButtonStyle.success, row=2
    )
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await (await self.sustained_interaction.original_response()).delete()
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        if not sett:
            return
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["welcome_message"] = self.welcome_message
        await self.bot.settings.update_by_id(sett)



class ERLCStats(discord.ui.View):
    def __init__(self, bot, user_id, guild_id):
        super().__init__(timeout=600.0)
        self.bot = bot
        self.value = None
        self.user_id = user_id
        self.guild_id = guild_id

    @discord.ui.button(label="Create", style=discord.ButtonStyle.success, row=2)
    async def create_stats(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):

        if interaction.user.id == self.user_id:
            modal = CreateERLCStats(self.bot, self.user_id, self.guild_id)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Create ER:LC Statistics",
                    description="Select a voice channel to set as a statistics channel.",
                    color=BLANK_COLOR,
                ).set_author(
                    name=interaction.guild.name,
                    icon_url=(
                        interaction.guild.icon.url if interaction.guild.icon else ""
                    ),
                ),
                view=modal,
                ephemeral=True,
            )

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.blurple, row=2)
    async def edit_stats(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = EditERLCStats(self.bot, self.user_id, self.guild_id)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Edit ER:LC Statistics",
                    description="Select a voice channel to edit statistics.",
                    color=BLANK_COLOR,
                ).set_author(
                    name=interaction.guild.name,
                    icon_url=(
                        interaction.guild.icon.url if interaction.guild.icon else ""
                    ),
                ),
                view=modal,
                ephemeral=True,
            )

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, row=2)
    async def delete_stats(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            msg_embed = interaction.message.embeds[0]

            modal = DeleteERLCStats(
                self.bot, self.user_id, self.guild_id, embed=msg_embed
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Delete ER:LC Statistics",
                    description="Select a voice channel to remove from statistics.",
                    color=BLANK_COLOR,
                ).set_author(
                    name=interaction.guild.name,
                    icon_url=(
                        interaction.guild.icon.url if interaction.guild.icon else ""
                    ),
                ),
                view=modal,
                ephemeral=True,
            )

    @discord.ui.button(
        label="View Variables", style=discord.ButtonStyle.secondary, row=2
    )
    async def view_variables(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            embed = discord.Embed(
                description=(
                    "With **ERM Statistics Check**, you can use custom variables to adapt to the current circumstances when the statistics is updated.\n"
                    "`{user}` - Mention of the person using the command.\n"
                    "`{username}` - Name of the person using the command.\n"
                    "`{display_name}` - Display name of the person using the command.\n"
                    "`{time}` - Timestamp format of the time of the command execution.\n"
                    "`{server}` - Name of the server this is being ran in.\n"
                    "`{channel}` - Mention of the channel the command is being ran in.\n"
                    "`{prefix}` - The custom prefix of the bot.\n"
                    "`{onduty}` - Number of staff which are on duty within your server.\n"
                    "\n**PRC Specific Variables**\n"
                    "`{join_code}` - Join Code of the ERLC server\n"
                    "`{players}` - Current players in the ERLC server\n"
                    "`{max_players}` - Maximum players of the ERLC server\n"
                    "`{queue}` - Number of players in the queue\n"
                    "`{staff}` - Number of staff members in-game\n"
                    "`{mods}` - Number of mods in-game\n"
                    "`{admins}` - Number of admins in-game\n"
                ),
                color=BLANK_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ShiftTypeCreator(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        dataset: dict,
        option: typing.Literal["create", "edit"],
        preset_values: dict | None = None,
    ):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.restored_interaction = None
        self.dataset = dataset
        self.cancelled = None
        self.option = option

        for key, value in (preset_values or {}).items():
            for item in self.children:
                if isinstance(item, discord.ui.RoleSelect) or isinstance(
                    item, discord.ui.ChannelSelect
                ):
                    if item.placeholder == key:
                        item.default_values = value

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return False

    async def refresh_ui(self, message: discord.Message):
        embed = discord.Embed(
            title=f"{self.option.title()} a Shift Type",
            description=(
                f"> **Name:** {self.dataset['name']}\n"
                f"> **ID:** {self.dataset['id']}\n"
                f"> **Shift Channel:** {'<#{}>'.format(self.dataset.get('channel', None)) if self.dataset.get('channel', None) is not None else 'Not set'}\n"
                f"> **Nickname Prefix:** {self.dataset.get('nickname') or 'Not set'}\n"
                f"> **On-Duty Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('role', [])]) or 'Not set'}\n"
                f"> **Break Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('break_roles', [])]) or 'Not set'}\n"
                f"> **Access Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('access_roles', [])]) or 'Not set'}\n\n\n"
                f"Access Roles are roles that are able to freely use this Shift Type and are able to go on-duty as this Shift Type. If an access role is selected, an individual must have it to go on-duty with this Shift Type."
            ),
            color=BLANK_COLOR,
        )

        if all([self.dataset.get("channel") is not None]):
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.label == "Finish":
                        item.disabled = False
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.label == "Finish":
                        item.disabled = True

        await message.edit(embed=embed, view=self)

    @discord.ui.select(
        cls=discord.ui.RoleSelect, placeholder="On-Duty Roles", row=0, max_values=25
    )  # changed to On-Duty Role for parity with the other select
    async def on_duty_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        # secvuln: prevention
        highest_role_pos = max([i.position for i in interaction.user.roles])
        compared_role_pos = max([role.position for role in select.values])
        if (
            interaction.user.id != interaction.guild.owner_id
            and highest_role_pos < compared_role_pos
        ):
            # we're not allowing this ...
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Security Concern",
                    description="You cannot choose an On-Duty Role that is higher than your maximum role.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            old_select = select
            select.default_values = list(
                filter(lambda x: x.position < highest_role_pos, select.values)
            )
            try:
                await self.refresh_ui(interaction.message)
            except discord.NotFound:
                await self.refresh_ui(
                    await self.restored_interaction.original_response()
                )
            return

        await interaction.response.defer()

        self.dataset["role"] = [i.id for i in select.values]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Break Roles",
        row=1,
        min_values=0,
        max_values=25,
    )  # changed to On-Duty Role for parity with the other select
    async def break_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        # secvuln: prevention
        highest_role_pos = max([i.position for i in interaction.user.roles])
        compared_role_pos = max(
            [role.position for role in select.values] or [0]
        )  # safety for deselection!
        if (
            interaction.user.id != interaction.guild.owner_id
            and highest_role_pos < compared_role_pos
        ):
            # we're not allowing this ...
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Security Concern",
                    description="You cannot choose a Break Role that is higher than your maximum role.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            old_select = select
            select.default_values = list(
                filter(lambda x: x.position < highest_role_pos, select.values)
            )
            try:
                await self.refresh_ui(interaction.message)
            except discord.NotFound:
                await self.refresh_ui(
                    await self.restored_interaction.original_response()
                )
            return

        await interaction.response.defer()

        self.dataset["break_roles"] = [i.id for i in select.values]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Access Roles",
        row=2,
        max_values=25,
        min_values=0,
    )
    async def access_roles_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        await interaction.response.defer()

        self.dataset["access_roles"] = [i.id for i in select.values]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Shift Channel",
        row=3,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        await interaction.response.defer()

        self.dataset["channel"] = [i.id for i in select.values][0]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.button(label="Edit Nickname Prefix", row=4)
    async def edit_nickname_prefix(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = CustomModal(
            "Edit Nickname Prefix",
            [
                (
                    "nickname_prefix",
                    discord.ui.TextInput(
                        label="Nickname Prefix", max_length=20, required=False
                    ),
                )
            ],
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        try:
            chosen_identifier = modal.nickname_prefix.value
        except ValueError:
            return

        if not chosen_identifier:
            return

        self.dataset["nickname"] = chosen_identifier
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This Shift Type has not been created.",
                color=BLANK_COLOR,
            ),
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except discord.NotFound:
            await (await self.restored_interaction.original_response()).delete()
        self.stop()

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, disabled=True, row=4
    )
    async def finish(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer()
        self.cancelled = False
        self.stop()


class RoleQuotaCreator(discord.ui.View):
    def __init__(self, bot, user_id: int, dataset: dict):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.bot = bot
        self.restored_interaction = None
        self.dataset = dataset
        self.cancelled = None

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return False

    async def refresh_ui(self, message: discord.Message):
        embed = discord.Embed(
            title="Role Quota Creation",
            description=(
                f"> **Role:** {'<@&{}>'.format(self.dataset['role']) if self.dataset['role'] != 0 else 'Not set'}\n"
                f"> **Quota:** {td_format(datetime.timedelta(seconds=self.dataset['quota']))}\n"
            ),
            color=BLANK_COLOR,
        )

        if all([self.dataset.get("role") != 0, self.dataset.get("quota") != 0]):
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.label == "Finish":
                        item.disabled = False
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.label == "Finish":
                        item.disabled = True

        await message.edit(embed=embed, view=self)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Binded Role",
        row=0,
        max_values=1,
        min_values=0,
    )
    async def mentioned_roles_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        if len(select.values) == 0:
            return await interaction.response.defer(thinking=False)

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        already_roles = []
        for item in settings.get("shift_management", {}).get("role_quotas", []):
            already_roles.append(item["role"])
        self.dataset["role"] = select.values[0].id if select.values else 0
        if self.dataset["role"] in already_roles:
            self.dataset["role"] = 0

        if self.dataset["role"] == 0:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unavailable Role",
                    description="This role already has a specified quota attached to it.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.defer()
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.button(label="Set Quota", row=1)
    async def set_quota(self, interaction: discord.Interaction, button: discord.Button):
        quota_hours = self.dataset["quota"]
        self.modal = CustomModal(
            "Quota",
            [
                (
                    "quota",
                    discord.ui.TextInput(
                        label="Quota",
                        placeholder="This value will be used to judge whether a staff member has completed quota.",
                        default=f"{td_format(datetime.timedelta(seconds=quota_hours))}",
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()

        try:
            seconds = time_converter(self.modal.quota.value)
        except ValueError:
            return

        self.dataset["quota"] = seconds
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This Role Quota has not been created.",
                color=BLANK_COLOR,
            ),
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except discord.NotFound:
            await (await self.restored_interaction.original_response()).delete()
        self.stop()

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, disabled=True, row=3
    )
    async def finish(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer()
        self.cancelled = False
        self.stop()

# CONFIG
class BasicConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        return await super().interaction_check(interaction)

    @discord.ui.select(
        cls=discord.ui.RoleSelect, placeholder="Staff Roles", row=0, max_values=25
    )
    async def staff_role_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id
        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Staff Roles have been set to {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        cls=discord.ui.RoleSelect, placeholder="Admin Role", row=1, max_values=25
    )
    async def admin_role_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["admin_role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Admin Role has been set to {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Management Roles",
        row=2,
        max_values=25,
        min_values=0,
    )
    async def management_role_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["management_role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Management Roles have been set to {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        placeholder="Prefix",
        row=3,
        options=[
            discord.SelectOption(
                label="!", description="Use '!' as your custom prefix."
            ),
            discord.SelectOption(
                label=">", description="Use '>' as your custom prefix."
            ),
            discord.SelectOption(
                label="?", description="Use '?' as your custom prefix."
            ),
            discord.SelectOption(
                label=":", description="Use ':' as your custom prefix."
            ),
            discord.SelectOption(
                label="-", description="Use '-' as your custom prefix."
            ),
        ],
        max_values=1,
    )
    async def prefix_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["customisation"]["prefix"] = select.values[0]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Prefix has been set to {select.values[0]}.",
        )
        for i in select.options:
            i.default = False


# class PunishmentTypesConfiguration(discord.ui.View):
#     def __init__(self, bot, user_id: int, given_data: list):
#             # Init vars
#             self.bot = bot
#             self.user_id = user_id
#             self.given_data = given_data
#
#             # TODO: match given data -> embed structure
#
#     async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
#         if interaction.user.id == self.user_id:
#             return True
#         else:
#             await interaction.response.send_message(embed=discord.Embed(
#                 title="Not Permitted",
#                 description="You are not permitted to interact with these buttons.",
#                 color=BLANK_COLOR
#             ), ephemeral=True)
#             return False
#
#     @discord.ui.select(options=[
#         discord.SelectOption(
#             label="Add Type",
#             description="Add a Punishment Type",
#             value="add"
#         ),
#         discord.SelectOption(
#             label="Modify Type",
#             description="Change some settings about a punishment type",
#             value="modify"
#         ),
#         discord.SelectOption(
#             label="Delete Type",
#             description="Delete a punishment type",
#             value="delete"
#         )
#     ])


class LOAConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.RoleSelect, placeholder="LOA Role", row=1, max_values=25
    )
    async def loa_role_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["loa_role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"LOA Role has been set to {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="LOA Channel",
        row=2,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def loa_channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["channel"] = select.values[0].id
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"LOA Channel has been set to <#{select.values[0].id}>.",
        )

    @discord.ui.select(
        placeholder="LOA Requests",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="LOA Requests are enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="LOA Requests are disabled.",
            ),
        ],
        max_values=1,
    )
    async def enabled_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"LOA Requests have been {'enabled' if select.values[0] == 'enabled' else 'disabled'}.",
        )
        for i in select.options:
            i.default = False


class ExtendedShiftOptions(discord.ui.View):
    def __init__(self, bot, associated_defaults: list):
        super().__init__(timeout=None)
        self.modal = None
        self.bot = bot
        self.modal_default = 0
        self.nickname_default = None
        self.quota_default = None

        for label, defaults in associated_defaults:
            if label == "max_staff":
                self.modal_default = defaults
                continue
            if label == "nickname_prefix":
                self.nickname_default = defaults
                continue
            if label == "quota":
                self.quota_default = defaults
                continue
            if label == "Break Roles":
                for item in self.children:
                    if (
                        isinstance(item, discord.ui.Select)
                        and item.placeholder == "Break Roles"
                    ):
                        item.default_values = defaults
                continue
            use_configuration = None
            if isinstance(defaults[0], list):
                if defaults[0][0] == "CUSTOM_CONF":
                    configurator = defaults[0]
                    match_configurator = configurator[1]
                    if match_configurator.get("_FIND_BY_LABEL") is True:
                        items = defaults[1:]
                        use_configuration = {
                            "configuration": match_configurator,
                            "matchables": items,
                        }

            item = None
            for iterating_item in self.children:
                if getattr(iterating_item, "label", None) is None:
                    if iterating_item.placeholder == label:
                        item = iterating_item
                        break
                else:
                    if iterating_item.label == label:
                        item = iterating_item
                        break
            if use_configuration is None:
                for index, defa in enumerate(defaults):
                    if defa is None:
                        defaults[index] = 0
                item.default_values = [i for i in defaults if i != 0]
            else:
                found_values = []
                for val in use_configuration["matchables"]:
                    if isinstance(item, discord.ui.Select):
                        if (
                            use_configuration["configuration"].get(
                                "_FIND_BY_LABEL", False
                            )
                            is True
                        ):
                            found_value = [i for i in item.options if i.label == val][0]
                            if not found_value:
                                continue
                            found_values.append(found_value)

                if isinstance(item, discord.ui.Select):
                    for val in found_values:
                        find_index = 0
                        for index, option in enumerate(item.options):
                            if option == val:
                                find_index = index
                                break
                        new_opt = item.options[find_index]
                        new_opt.default = True
                        item.options[find_index] = new_opt

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Break Roles",
        max_values=25,
        min_values=0,
    )
    async def shift_role_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        # secvuln: prevention
        highest_role_pos = max([i.position for i in interaction.user.roles])
        compared_role_pos = max([role.position for role in select.values])
        if (
            interaction.user.id != interaction.guild.owner_id
            and highest_role_pos <= compared_role_pos
        ):
            # we're not allowing this ...
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Security Concern",
                    description="You cannot choose a Break Role that is higher than your maximum role.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            select.default_values = list(
                filter(lambda x: x.position < highest_role_pos, select.values)
            )
            await interaction.message.edit(view=self)
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["shift_management"]["break_roles"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Break Role has been set to {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.button(label="Set Maximum Staff Online", row=4)
    async def set_maximum_staff_online(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.modal = CustomModal(
            "Maximum Staff",
            [
                (
                    "max_staff",
                    discord.ui.TextInput(
                        label="Maximum Staff Online",
                        placeholder="This is the amount of staff members that can be online at one time.",
                        default=str(self.modal_default),
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        max_staff = self.modal.max_staff.value
        max_staff = int(max_staff.strip())

        bot = self.bot
        sett = await bot.settings.find_by_id(interaction.guild.id)
        sett["shift_management"]["maximum_staff"] = max_staff
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Maximum Staff Online has been set to {max_staff}.",
        )
        self.modal_default = max_staff

    @discord.ui.button(label="Set Nickname Prefix", row=3)
    async def set_nickname_prefix(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.modal = CustomModal(
            "Nickname Prefix",
            [
                (
                    "nickname_prefix",
                    discord.ui.TextInput(
                        label="Nickname Prefix",
                        placeholder="The nickname prefix that will be used when someone goes On-Duty.",
                        default=str(self.nickname_default),
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        nickname_prefix = self.modal.nickname_prefix.value

        bot = self.bot
        sett = await bot.settings.find_by_id(interaction.guild.id)
        sett["shift_management"]["nickname_prefix"] = nickname_prefix
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Nickname Prefix has been set to {nickname_prefix}.",
        )
        self.nickname_default = nickname_prefix

    @discord.ui.button(label="Set Quota", row=2)
    async def set_quota(self, interaction: discord.Interaction, button: discord.Button):
        quota_hours = self.quota_default
        self.modal = CustomModal(
            "Quota",
            [
                (
                    "quota",
                    discord.ui.TextInput(
                        label="Quota",
                        placeholder="This value will be used to judge whether a staff member has completed quota.",
                        default=td_format(datetime.timedelta(seconds=quota_hours)),
                        required=False,
                    ),
                )
            ],
            epher_args={"ephemeral": True},
        )

        await interaction.response.send_modal(self.modal)
        await self.modal.wait()

        try:
            seconds = time_converter(self.modal.quota.value)
        except ValueError:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Time",
                    description="You provided an invalid time format.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        bot = self.bot
        sett = await bot.settings.find_by_id(interaction.guild.id)
        sett["shift_management"]["quota"] = seconds
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Quota has been set to {td_format(datetime.timedelta(seconds=seconds))}.",
        )
        self.quota_default = seconds


class ShiftConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="On-Duty Role",
        row=2,
        max_values=25,
        min_values=0,
    )
    async def shift_role_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        # secvuln: prevention
        highest_role_pos = max([i.position for i in interaction.user.roles])
        compared_role_pos = max([role.position for role in select.values])
        if (
            interaction.user.id != interaction.guild.owner_id
            and highest_role_pos <= compared_role_pos
        ):
            # we're not allowing this ...
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Security Concern",
                    description="You cannot choose an On-Duty role that is higher than your maximum role.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            select.default_values = list(
                filter(lambda x: x.position < highest_role_pos, select.values)
            )
            await interaction.message.edit(view=self)
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["shift_management"]["role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"On-Duty Role has been set to {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Shift Channel",
        row=1,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def shift_channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["shift_management"]["channel"] = select.values[0].id
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Shift Channel has been set to <#{select.values[0].id}>.",
        )

    @discord.ui.select(
        placeholder="Shift Management",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="Shift Management is enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="Shift Management is disabled.",
            ),
        ],
        max_values=1,
    )
    async def enabled_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["shift_management"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            bot,
            interaction.guild,
            interaction.user,
            f"Shift Management has been {'enabled' if select.values[0] == 'enabled' else 'disabled'}.",
        )
        for i in select.options:
            i.default = False

    @discord.ui.button(label="More Options", row=3)
    async def more_options(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        new_view = ExtendedShiftOptions(
            self.bot,
            [
                ("max_staff", sett["shift_management"].get("maximum_staff", 0)),
                ("quota", sett["shift_management"].get("quota", 0)),
                (
                    "nickname_prefix",
                    sett["shift_management"].get("nickname_prefix", ""),
                ),
                (
                    "Break Roles",
                    [
                        discord.utils.get(interaction.guild.roles, id=i)
                        for i in sett["shift_management"].get("break_roles", [])
                    ],
                ),
            ],
        )
        await interaction.response.send_message(view=new_view, ephemeral=True)

    @discord.ui.button(label="Shift Types", row=3)
    async def shift_types(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        shift_types = settings.get("shift_types", {}).get("types", [])

        embed = discord.Embed(title="Shift Types", color=BLANK_COLOR)
        for item in shift_types:
            embed.add_field(
                name=f"{item['name']}",
                value=(
                    f"> **Name:** {item['name']}\n"
                    f"> **ID:** {item['id']}\n"
                    f"> **Channel:** <#{item['channel']}>\n"
                    f"> **Nickname Prefix:** {item.get('nickname') or 'None'}\n"
                    f"> **Access Roles:** {','.join(['<@&{}>'.format(role) for role in item.get('access_roles') or []]) or 'None'}\n"
                    f"> **On-Duty Role:** {','.join(['<@&{}>'.format(role) for role in item.get('role', [])]) or 'None'}"
                ),
                inline=False,
            )

        if len(embed.fields) == 0:
            embed.add_field(
                name="No Shift Types",
                value="There are no shift types on this server.",
                inline=False,
            )
        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )

        view = ShiftTypeManagement(interaction.user.id)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        await view.wait()

        if view.value == "edit":
            selected_item = None
            for item in shift_types:
                if item["name"] == view.name_for_creation:
                    selected_item = item
                    break

            if not selected_item:
                return await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="Incorrect Shift Type",
                        description="This shift type is incorrect or invalid.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            data = selected_item

            embed = discord.Embed(
                title="Edit a Shift Type",
                description=(
                    f"> **Name:** {data['name']}\n"
                    f"> **ID:** {data['id']}\n"
                    f"> **Shift Channel:** {'<#{}>'.format(data.get('channel', None)) if data.get('channel', None) is not None else 'Not set'}\n"
                    f"> **Nickname Prefix:** {data.get('nickname') or 'None'}\n"
                    f"> **On-Duty Roles:** {', '.join(['<@&{}>'.format(r) for r in data.get('role', [])]) or 'Not set'}\n"
                    f"> **Break Roles:** {', '.join(['<@&{}>'.format(r) for r in data.get('break_roles', [])]) or 'Not set'}\n"
                    f"> **Access Roles:** {', '.join(['<@&{}>'.format(r) for r in data.get('access_roles', [])]) or 'Not set'}\n\n\n"
                    f"Access Roles are roles that are able to freely use this Shift Type and are able to go on-duty as this Shift Type. If an access role is selected, an individual must have it to go on-duty with this Shift Type."
                ),
                color=BLANK_COLOR,
            )

            roles = list(
                filter(
                    lambda x: x is not None,
                    [
                        discord.utils.get(interaction.guild.roles, id=i)
                        for i in data.get("role", [])
                    ],
                )
            )
            break_roles = list(
                filter(
                    lambda x: x is not None,
                    [
                        discord.utils.get(interaction.guild.roles, id=i)
                        for i in data.get("break_roles", [])
                    ],
                )
            )

            access_roles = list(
                filter(
                    lambda x: x is not None,
                    [
                        discord.utils.get(interaction.guild.roles, id=i)
                        for i in data.get("access_roles", [])
                    ],
                )
            )
            shift_channel = list(
                filter(
                    lambda x: x is not None,
                    [
                        discord.utils.get(
                            interaction.guild.channels, id=data.get("channel", 0)
                        )
                    ],
                )
            )

            view = ShiftTypeCreator(
                interaction.user.id,
                data,
                "edit",
                {
                    "On-Duty Roles": roles,
                    "Break Roles": break_roles,
                    "Access Roles": access_roles,
                    "Shift Channel": shift_channel,
                },
            )
            view.restored_interaction = interaction
            msg = await interaction.original_response()
            await msg.edit(view=view, embed=embed)
            await view.wait()
            if view.cancelled is True:
                return

            dataset = settings.get("shift_types", {}).get("types", [])

            for index, item in enumerate(dataset):
                if item["id"] == view.dataset["id"]:
                    dataset[index] = view.dataset
                    break
            if not settings.get("shift_types"):
                settings["shift_types"] = {}
                settings["shift_types"]["types"] = dataset
            else:
                settings["shift_types"]["types"] = dataset

            await self.bot.settings.update_by_id(settings)
            await msg.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Shift Type Edited",
                    description="Your shift type has been edited!",
                    color=GREEN_COLOR,
                ),
                view=None,
            )
            return

        if view.value == "create":
            data = {
                "id": next(generator),
                "name": view.name_for_creation,
                "channel": None,
                "roles": [],
            }
            embed = discord.Embed(
                title="Shift Type Creation",
                description=(
                    f"> **Name:** {data['name']}\n"
                    f"> **ID:** {data['id']}\n"
                    f"> **Shift Channel:** {'<#{}>'.format(data.get('channel', None)) if data.get('channel', None) is not None else 'Not set'}\n"
                    f"> **Nickname Prefix:** {data.get('nickname') or 'None'}\n"
                    f"> **On-Duty Roles:** {', '.join(['<@&{}>'.format(r) for r in data.get('role', [])]) or 'Not set'}\n"
                    f"> **Access Roles:** {', '.join(['<@&{}>'.format(r) for r in data.get('access_roles', [])]) or 'Not set'}\n\n\n"
                    f"Access Roles are roles that are able to freely use this Shift Type and are able to go on-duty as this Shift Type. If an access role is selected, an individual must have it to go on-duty with this Shift Type."
                ),
                color=BLANK_COLOR,
            )

            view = ShiftTypeCreator(interaction.user.id, data, "create")
            view.restored_interaction = interaction
            msg = await interaction.original_response()
            await msg.edit(view=view, embed=embed)
            await view.wait()
            if view.cancelled is True:
                return

            dataset = settings.get("shift_types", {}).get("types", [])

            dataset.append(view.dataset)
            if not settings.get("shift_types"):
                settings["shift_types"] = {}
                settings["shift_types"]["types"] = dataset
            else:
                settings["shift_types"]["types"] = dataset

            await self.bot.settings.update_by_id(settings)
            await msg.edit(
                embed=discord.Embed(
                    title="<:success:1163149118366040106> Shift Type Created",
                    description="Your shift type has been created!",
                    color=GREEN_COLOR,
                ),
                view=None,
            )
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"Shift Type Created: {view.dataset['name']}",
            )
            return
        elif view.value == "delete":
            try:
                type_id = int(view.selected_for_deletion.strip())
            except ValueError:
                return await (await interaction.original_response()).edit(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="The ID you have provided is not associated with a shift type.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            shift_types = settings.get("shift_types", {}).get("types", [])
            if len(shift_types) == 0:
                return await (await interaction.original_response()).edit(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="The ID you have provided is not associated with a shift type.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            if type_id not in [t["id"] for t in shift_types]:
                return await (await interaction.original_response()).edit(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="The ID you have provided is not associated with a shift type.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            for item in shift_types:
                if item["id"] == type_id:
                    shift_types.remove(item)
                    break

            if not settings.get("shift_types"):
                settings["shift_types"] = {}

            settings["shift_types"]["types"] = shift_types
            await self.bot.settings.update_by_id(settings)
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"Shift Type Deleted: {item['name']}",
            )
            msg = await interaction.original_response()
            await msg.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Shift Type Deleted",
                    description="Your shift type has been deleted!",
                    color=GREEN_COLOR,
                ),
                view=None,
            )

    @discord.ui.button(label="Role Quotas", row=3)
    async def role_quotas(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        role_quotas = settings.get("shift_management").get("role_quotas", [])

        embed = discord.Embed(title="Role Quotas", description="", color=BLANK_COLOR)
        for item in role_quotas:
            role_id, particular_quota = item["role"], item["quota"]
            # role = interaction.guild.get_role(role_id)
            try:
                roles = await interaction.guild.fetch_roles()
                role = discord.utils.get(roles, id=role_id)
            except discord.HTTPException:
                continue

            if not role:
                continue
            embed.description += f"{role.mention} `{role_id}` • {td_format(datetime.timedelta(seconds=particular_quota))}\n"

        if len(embed.description) == 0:
            embed.add_field(
                name="No Role Quotas",
                value="There are no role quotas in this server.",
                inline=False,
            )
        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )

        view = RoleQuotaManagement(interaction.user.id)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        await view.wait()
        if view.value == "create":
            data = {"role": 0, "quota": 0}
            embed = discord.Embed(
                title="Role Quota Creation",
                description=(
                    f"> **Role:** {'<@&{}>'.format(data['role']) if data['role'] != 0 else 'Not set'}\n"
                    f"> **Quota:** {td_format(datetime.timedelta(seconds=data['quota']))}\n"
                ),
                color=BLANK_COLOR,
            )

            view = RoleQuotaCreator(self.bot, interaction.user.id, data)
            view.restored_interaction = interaction
            msg = await interaction.original_response()
            await msg.edit(view=view, embed=embed)
            await view.wait()
            if view.cancelled is True:
                return

            dataset = settings.get("shift_management", {}).get("role_quotas", [])

            dataset.append(view.dataset)
            settings["shift_management"]["role_quotas"] = dataset

            await self.bot.settings.update_by_id(settings)
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"Role Quota Created: {view.dataset['role']} | Quota: {td_format(datetime.timedelta(seconds=view.dataset['quota']))}",
            )
            await msg.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Role Quota Created",
                    description="Your Role Quota has been created!",
                    color=GREEN_COLOR,
                ),
                view=None,
            )
        elif view.value == "delete":
            try:
                type_id = int(view.selected_for_deletion.strip())
            except ValueError:
                return await (await interaction.original_response()).edit(
                    embed=discord.Embed(
                        title="Invalid Role ID",
                        description="The ID you have provided is not associated with a Role Quota.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            role_quotas = settings.get("shift_management", {}).get("role_quotas", [])
            if len(role_quotas) == 0:
                return await (await interaction.original_response()).edit(
                    embed=discord.Embed(
                        title="Invalid Role ID",
                        description="The ID you have provided is not associated with a Role Quota.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            if type_id not in [t["role"] for t in role_quotas]:
                return await (await interaction.original_response()).edit(
                    embed=discord.Embed(
                        title="Invalid Role ID",
                        description="The ID you have provided is not associated with a Role Quota.",
                        color=BLANK_COLOR,
                    ),
                    view=None,
                )

            for item in role_quotas:
                if item["role"] == type_id:
                    role_quotas.remove(item)
                    break

            settings["shift_management"]["role_quotas"] = role_quotas
            await self.bot.settings.update_by_id(settings)
            msg = await interaction.original_response()
            await config_change_log(
                self.bot,
                interaction.guild,
                interaction.user,
                f"Role Quota Deleted: {item['role']} | Quota: {td_format(datetime.timedelta(seconds=item['quota']))}",
            )
            await msg.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Role Quota Deleted",
                    description="Your Role Quota has been deleted!",
                    color=GREEN_COLOR,
                ),
                view=None,
            )


class ERMCommandLog(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="ERM Log Channel",
        row=0,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def command_log_channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        try:
            sett["staff_management"]["erm_log_channel"] = select.values[0].id
        except KeyError:
            sett["staff_management"] = {"erm_log_channel": select.values[0].id}
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"ERM Log Channel Set: <#{select.values[0].id}>",
        )


class RAConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="RA Role",
        row=2,
        max_values=25,
        min_values=0,
    )
    async def ra_role_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["staff_management"]["ra_role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"RA Role Set: {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )


class ExtendedPunishmentConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Kick Channel",
        row=0,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def kick_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot

        sett = await bot.settings.find_by_id(guild_id)
        sett["punishments"]["kick_channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Kick Channel Set: <#{select.values[0].id}>  ",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Ban Channel",
        row=1,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def ban_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot

        sett = await bot.settings.find_by_id(guild_id)
        sett["punishments"]["ban_channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Ban Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="BOLO Channel",
        row=2,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def bolo_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot

        sett = await bot.settings.find_by_id(guild_id)
        sett["punishments"]["bolo_channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"BOLO Channel Set: <#{select.values[0].id}>",
        )


class PunishmentsConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        placeholder="ROBLOX Punishments",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="ROBLOX Punishments are enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="ROBLOX Punishments are disabled.",
            ),
        ],
        max_values=1,
    )
    async def enabled_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["punishments"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"ROBLOX Punishments {select.values[0]}.",
        )
        for i in select.options:
            i.default = False

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Punishments Channel",
        row=1,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def punishment_channel_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        sett["punishments"]["channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Punishments Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.button(label="More Options", row=2)
    async def more_options(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        new_view = ExtendedPunishmentConfiguration(
            self.bot,
            interaction.user.id,
            [
                (
                    "Kick Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("punishments", {}).get("kick_channel", 0),
                        )
                    ],
                ),
                (
                    "Ban Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("punishments", {}).get("ban_channel", 0),
                        )
                    ],
                ),
                (
                    "BOLO Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("punishments", {}).get("bolo_channel", 0),
                        )
                    ],
                ),
            ],
        )
        await interaction.response.send_message(view=new_view, ephemeral=True)

    @discord.ui.button(label="Default Punishments", row=2)
    async def default_punishments(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        sett = await self.bot.punishment_types.find_by_id(interaction.guild.id)

        view = defaultPunishments(self.bot, sett, interaction.user.id)
        await interaction.response.send_message(view=view, ephemeral=True)

class defaultPunishments(discord.ui.View):
    def __init__(self, bot, sett, user_id):
        super().__init__()
        self.bot = bot
        self.sett = sett
        self.user_id = user_id

        self.default_punishments = ["warning", "kick", "ban", "bolo"]

        raw_punishments = {
            p["name"]: p.get("enabled", False)
            for p in sett.get("default_punishments", [])
        }

        self.warning_enabled = raw_punishments.get("warning", True)
        self.kick_enabled = raw_punishments.get("kick", True)
        self.ban_enabled = raw_punishments.get("ban", True)
        self.bolo_enabled = raw_punishments.get("bolo", True)

        options = [
            discord.SelectOption(label="Warning", value="Warning", default=self.warning_enabled),
            discord.SelectOption(label="Kick", value="Kick", default=self.kick_enabled),
            discord.SelectOption(label="Ban", value="Ban", default=self.ban_enabled),
            discord.SelectOption(label="BOLO", value="BOLO", default=self.bolo_enabled),
        ]

        select = discord.ui.Select(
            placeholder="Select a punishment",
            options=options,
            max_values=4,
            min_values=0,
        )

        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected = [i.lower() for i in interaction.data["values"]]

        self.sett["default_punishments"] = [
            {"name": name, "enabled": name in selected}
            for name in self.default_punishments
        ]

        await self.bot.punishment_types.update_by_id(
            self.sett
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Default Punishments Updated",
                description="The default punishments have been updated.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

class GameSecurityConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        placeholder="Game Security",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="Game Security is enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="Game Security is disabled.",
            ),
        ],
        max_values=1,
    )
    async def enabled_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_security"):
            sett["game_security"] = {}
        sett["game_security"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Game Security {select.values[0]}.",
        )
        for i in select.options:
            i.default = False

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Webhook Channel",
        row=1,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def security_webhook_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_security"):
            sett["game_security"] = {}
        sett["game_security"]["webhook_channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Game Security Webhook Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Alert Channel",
        row=2,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def security_alert_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_security"):
            sett["game_security"] = {}
        sett["game_security"]["channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Game Security Alert Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Mentionables",
        row=3,
        max_values=25,
        min_values=0,
    )
    async def security_mentionables(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_security"):
            sett["game_security"] = {}
        sett["game_security"]["role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Game Security Mentionables Set: {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

class WhitelistVehiclesManagement(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id,
        enable_vehicle_restrictions=None,
        whitelisted_vehicles_roles=None,
        whitelisted_vehicle_alert_channel=0,
        whitelisted_vehicles=None,
        associated_defaults=None,
        alert_message=None,
    ):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.guild_id = guild_id
        self.enable_vehicle_restrictions = enable_vehicle_restrictions
        self.whitelisted_vehicles_roles = whitelisted_vehicles_roles or []
        self.whitelisted_vehicle_alert_channel = whitelisted_vehicle_alert_channel
        self.whitelisted_vehicles = whitelisted_vehicles or []
        self.alert_message = alert_message or ""
        associated_defaults = associated_defaults or []

        # Fetch roles from the guild using their IDs
        self.whitelisted_vehicles_roles_objs = [
            self.bot.get_guild(self.guild_id).get_role(role_id)
            for role_id in self.whitelisted_vehicles_roles
            if self.bot.get_guild(self.guild_id).get_role(role_id) is not None
        ]

        self.enable_vehicle_restrictions_button = discord.ui.Button(
            label="Vehicle Restrictions",
            style=discord.ButtonStyle.secondary,
            row=3,
        )

        # Initialize the select menus and button
        self.whitelisted_vehicles_roles_select = discord.ui.RoleSelect(
            placeholder="Whitelisted Vehicles Roles",
            max_values=10,
            min_values=0,
            default_values=self.whitelisted_vehicles_roles_objs,
        )

        channel = self.bot.get_guild(self.guild_id).get_channel(
            self.whitelisted_vehicle_alert_channel
        )
        default_values = [channel] if channel else []

        self.whitelisted_vehicle_alert_channel_select = discord.ui.ChannelSelect(
            placeholder="Whitelisted Vehicle Alert Channel",
            max_values=1,
            min_values=0,
            channel_types=[discord.ChannelType.text],
            default_values=default_values,
        )

        self.add_vehicle_button = discord.ui.Button(
            label="Add Vehicle to Role", style=discord.ButtonStyle.secondary, row=2
        )

        self.add_message_button = discord.ui.Button(
            label="Add Alert Message", style=discord.ButtonStyle.secondary, row=2
        )

        self.add_item(self.whitelisted_vehicles_roles_select)
        self.add_item(self.whitelisted_vehicle_alert_channel_select)
        self.add_item(self.add_vehicle_button)
        self.add_item(self.add_message_button)
        self.add_item(self.enable_vehicle_restrictions_button)

        self.whitelisted_vehicles_roles_select.callback = self.create_callback(
            self.whitelisted_vehicles_roles_callback,
            self.whitelisted_vehicles_roles_select,
        )
        self.whitelisted_vehicle_alert_channel_select.callback = self.create_callback(
            self.whitelisted_vehicle_alert_channel_callback,
            self.whitelisted_vehicle_alert_channel_select,
        )
        self.add_vehicle_button.callback = self.create_callback(
            self.add_vehicle_to_role, self.add_vehicle_button
        )
        self.add_message_button.callback = self.create_callback(
            self.add_alert_message, self.add_message_button
        )
        self.enable_vehicle_restrictions_button.callback = self.create_callback(
            self.toggle_vehicle_restrictions, self.enable_vehicle_restrictions_button
        )

    def create_callback(self, func, component):
        async def callback(interaction: discord.Interaction):
            if isinstance(component, discord.ui.RoleSelect):
                return await func(interaction, component)
            elif isinstance(component, discord.ui.Button):
                return await func(interaction, component)
            elif isinstance(component, discord.ui.ChannelSelect):
                return await func(interaction, component)

        return callback

    async def toggle_vehicle_restrictions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {"vehicle_restrictions": {}}

        vehicle_restrictions = sett["ERLC"].get("vehicle_restrictions", {})
        vehicle_restrictions["enabled"] = not vehicle_restrictions.get("enabled", False)
        sett["ERLC"]["vehicle_restrictions"] = vehicle_restrictions
        await bot.settings.update_by_id(sett)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Vehicle Restrictions",
            value=f"If enabled, users will be alerted if they use a whitelisted vehicle without the correct roles.\n**Current Status:** {'Enabled' if vehicle_restrictions['enabled'] else 'Disabled'}",
        )
        await interaction.edit_original_response(embed=embed)

    async def whitelisted_vehicles_roles_callback(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {"vehicle_restrictions": {}}

        vehicle_restrictions = sett["ERLC"].get("vehicle_restrictions", {})
        vehicle_restrictions["roles"] = [i.id for i in select.values]
        sett["ERLC"]["vehicle_restrictions"] = vehicle_restrictions
        await bot.settings.update_by_id(sett)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            5,
            name="Current Roles",
            value=(
                ", ".join([f"<@&{i.id}>" for i in select.values])
                if select.values
                else "None"
            ),
        )
        await interaction.edit_original_response(embed=embed)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Whitelisted Vehicles Roles Set: {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    async def whitelisted_vehicle_alert_channel_callback(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {"vehicle_restrictions": {}}

        vehicle_restrictions = sett["ERLC"].get("vehicle_restrictions", {})
        vehicle_restrictions["channel"] = select.values[0].id
        sett["ERLC"]["vehicle_restrictions"] = vehicle_restrictions
        await bot.settings.update_by_id(sett)
        embed = interaction.message.embeds[0]
        embed.set_field_at(6, name="Current Channel", value=f"<#{select.values[0].id}>")
        await interaction.edit_original_response(embed=embed)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Whitelisted Vehicle Alert Channel Set: <#{select.values[0].id}>",
        )

    async def add_vehicle_to_role(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild_id = interaction.guild.id
        bot = self.bot

        sett = await bot.settings.find_by_id(guild_id)
        existing_vehicles = (
            sett.get("ERLC", {}).get("vehicle_restrictions", {}).get("cars", [])
        )

        existing_vehicles_str = ", ".join(existing_vehicles)

        modal = CustomModal(
            "Add Vehicle to Role",
            [
                (
                    "vehicle",
                    discord.ui.TextInput(
                        label="Vehicle",
                        placeholder="e.g. Falcon Fission 2015, Navara Imperium 2020, etc",
                        default=existing_vehicles_str,
                        min_length=0,
                    ),
                )
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(modal)
        await modal.wait()

        if not modal.vehicle.value:
            return

        vehicles = [i.strip() for i in modal.vehicle.value.split(",")]
        if not vehicles:
            return

        if not sett.get("ERLC"):
            sett["ERLC"] = {"vehicle_restrictions": {}}
        try:
            sett["ERLC"]["vehicle_restrictions"]["cars"] = vehicles
        except KeyError:
            sett["ERLC"] = {"vehicle_restrictions": {"cars": vehicles}}
        await bot.settings.update_by_id(sett)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            7,
            name="Current Whitelisted Vehicles",
            value=", ".join(vehicles) if vehicles else "None",
        )
        await interaction.edit_original_response(embed=embed)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Whitelisted Vehicles Added: {', '.join(vehicles)}",
        )

    async def add_alert_message(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild_id = interaction.guild.id
        bot = self.bot

        sett = await bot.settings.find_by_id(guild_id)
        existing_message = (
            sett.get("ERLC", {}).get("vehicle_restrictions", {}).get("message", "")
        )

        modal = CustomModal(
            "Add Alert Message",
            [
                (
                    "message",
                    discord.ui.TextInput(
                        label="Message",
                        placeholder="e.g. You are not allowed to drive this vehicle. Please contact an admin for assistance.",
                        default=existing_message,
                        min_length=0,
                    ),
                )
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(modal)
        await modal.wait()

        if not modal.message.value:
            return

        if not sett.get("ERLC"):
            sett["ERLC"] = {"vehicle_restrictions": {}}
        try:
            sett["ERLC"]["vehicle_restrictions"]["message"] = modal.message.value
        except KeyError:
            sett["ERLC"] = {"vehicle_restrictions": {"message": modal.message.value}}
        await bot.settings.update_by_id(sett)
        embed = interaction.message.embeds[0]
        embed.set_field_at(8, name="Alert Message", value=modal.message.value)
        await interaction.edit_original_response(embed=embed)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Whitelisted Vehicle Alert Message Set: {modal.message.value}",
        )


class ERLCIntegrationConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        placeholder="Elevation Required",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="Elevated Permissions are required.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="Elevated Permissions are not required.",
            ),
        ],
        max_values=1,
    )
    async def priority_logging_enabled(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {
                "player_logs": 0,
                "kill_logs": 0,
                "elevation_required": True,
            }

        sett["ERLC"]["elevation_required"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Elevation Required {select.values[0]}",
        )
        for i in select.options:
            i.default = False

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Player Logs Channel",
        row=1,
        max_values=1,
        min_values=0,
    )
    async def player_logs_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {
                "player_logs": 0,
                "kill_logs": 0,
                "elevation_required": True,
            }
        sett["ERLC"]["player_logs"] = select.values[0].id if select.values else 0
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Player Logs Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Kill Logs Channel",
        row=2,
        max_values=1,
        min_values=0,
    )
    async def kill_logs_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {
                "player_logs": 0,
                "kill_logs": 0,
                "elevation_required": True,
            }
        sett["ERLC"]["kill_logs"] = select.values[0].id if select.values else 0
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Kill Logs Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.button(label="RDM Alerts", row=3)
    async def rdm_alerts(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        new_view = RDMERLCConfiguration(
            self.bot,
            interaction.user.id,
            [
                (
                    "RDM Mentionables",
                    [
                        discord.utils.get(interaction.guild.roles, id=i)
                        for i in (sett.get("ERLC", {}).get("rdm_mentionables") or [])
                    ],
                ),
                (
                    "RDM Alert Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("ERLC", {}).get("rdm_channel"),
                        )
                    ],
                ),
            ],
        )
        await interaction.response.send_message(view=new_view, ephemeral=True)

    @discord.ui.button(label="Automatic Shifts", row=3)
    async def automatic_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        auto_shift_data = settings.get("ERLC", {}).get(
            "automatic_shifts", {"enabled": False, "shift_type": "Default"}
        )

        embed = discord.Embed(
            title="Automatic Shifts", description="", color=BLANK_COLOR
        )
        for key, value in auto_shift_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {(value or 'Default') if isinstance(value, str) else ('<:check:1163142000271429662>' if value is True else '<:xmark:1166139967920164915>')}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        shift_types = (settings.get("shift_types", {}) or {}).get("types", []) or []
        view = AutomaticShiftConfiguration(
            self.bot, interaction, shift_types, auto_shift_data
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Remote ERM Commands", row=3)
    async def remote_commands(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        auto_shift_data = settings.get("ERLC", {}).get(
            "remote_commands", {"webhook_channel": None}
        )

        embed = discord.Embed(
            title="Remote Commands", description="", color=BLANK_COLOR
        )
        for key, value in auto_shift_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {'<#' + str(value) + '>' if isinstance(value, int) else 'None'}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        shift_types = (settings.get("shift_types", {}) or {}).get("types", []) or []
        view = RemoteCommandConfiguration(
            self.bot, interaction, shift_types, auto_shift_data
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="More Options", row=3)
    async def more_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        view = MoreERLCConfiguration(self.bot, await self.bot.settings.find_by_id(interaction.guild.id))

        embed = discord.Embed(
            title="More ER:LC Options",
            description="",
            color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )

        embed.description = (
            "**PM on Warning:** This option allows you to enable or disable PMs being sent to users when they receive a warning in ERLC.\n\n"
            "**Auto-Punish:** This option automatically kicks and bans* people in-game when the appropriate punishment is logged. Individuals will only be banned if the moderator holds the Admin Role or the Server Administrator permission in-game.\n\n"
            "**Welcome Messaging:** This feature allows you to configure a welcome message that will be sent to players when they join your server.\n\n"
            "**Vehicle Restrictions:** This feature allows you to manage vehicle restrictions in your server, including whitelisted vehicles and roles.\n\n"
            "**ER:LC Statistics:** This feature allows you to manage & setup Voice Channels to show the current stats of ER:LC in your server.\n\n"
            "**Automatic Discord Checks:** This feature allows you to configure automatic discord checks for ER:LC in your server & message players when they are not in the discord server.\n\n"
            "**Permission Sync:** This feature automatically gives users the Server Moderator and Server Administrator permissions when they go on shift, removing it when they go off shift."
        )

        await interaction.response.send_message(
            embed=embed,
            view=view
        )

class MoreERLCConfiguration(discord.ui.View):
    def __init__(self, bot, settings):
        super().__init__(timeout=None)
        self.bot = bot
        erlc_settings = settings.get("ERLC")
        auto_punish = erlc_settings.get("auto_punish", False)
        message_on_warning = erlc_settings.get("message_on_warning", False)
        for item in self.children:
            if isinstance(item, discord.ui.Select):
                if item.placeholder == "PM on Warning":
                    for choice in item.options:
                        if choice.value == "enabled" and message_on_warning:
                            choice.default = True
                        elif choice.value == "disabled" and not message_on_warning:
                            choice.default = True
                else:
                    for choice in item.options:
                        if choice.value == "enabled" and auto_punish:
                            choice.default = True
                        elif choice.value == "disabled" and not auto_punish:
                            choice.default = True

    @discord.ui.select(
        placeholder="PM on Warning",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="PM on Warning is enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="PM on Warning is disabled.",
            ),
        ],
    )
    async def message_on_warning(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["message_on_warning"] = bool(select.values[0].lower() == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"PM on Warning set: {select.values[0]}",
        )

    @discord.ui.select(
        placeholder="Auto-Punish",
        row=1,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="Auto-Punish is enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="Auto-Punish is disabled.",
            ),
        ],
    )
    async def auto_punish(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["auto_punish"] = bool(select.values[0].lower() == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Auto-Punish set: {select.values[0]}",
        )

    @discord.ui.button(label="Welcome Messaging", row=2)
    async def welcome_messaging(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        welcome_message = (settings.get("ERLC") or {}).get("welcome_message") or ""

        embed = discord.Embed(
            title="Welcome Messaging",
            description="*This module allows for a message to appear to players of your server when they initially join your server.*\n\n",
            color=BLANK_COLOR,
        )
        embed.description += f"**Welcome Message:** {welcome_message if welcome_message != '' else 'None'}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        view = WelcomeMessagingConfiguration(self.bot, interaction, welcome_message)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Vehicle Restrictions", row=2)
    async def vehicle_restrictions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        enable_vehicle_restrictions = (
            settings.get("ERLC", {})
            .get("vehicle_restrictions", {})
            .get("enabled", False)
        )
        vehicle_restrictions_roles = (
            settings.get("ERLC", {}).get("vehicle_restrictions", {}).get("roles", [])
        )
        vehicle_restrictions_channel = (
            settings.get("ERLC", {}).get("vehicle_restrictions", {}).get("channel", 0)
        )
        vehicle_restrictions_cars = (
            settings.get("ERLC", {}).get("vehicle_restrictions", {}).get("cars", [])
        )
        alert_message = (
            settings.get("ERLC", {}).get("vehicle_restrictions", {}).get("message", "")
        )

        view = WhitelistVehiclesManagement(
            self.bot,
            interaction.guild.id,
            enable_vehicle_restrictions=enable_vehicle_restrictions,
            whitelisted_vehicles_roles=vehicle_restrictions_roles,
            whitelisted_vehicle_alert_channel=vehicle_restrictions_channel,
            whitelisted_vehicles=vehicle_restrictions_cars,
            alert_message=alert_message,
        )
        embed = (
            discord.Embed(
                title="Whitelisted Vehicles", color=BLANK_COLOR, description=" "
            )
            .add_field(
                name="Vehicle Restrictions",
                value=f"If enabled, users will be alerted if they use a whitelisted vehicle without the correct roles.\n**Current Status:** {'Enabled' if enable_vehicle_restrictions else 'Disabled'}",
            )
            .add_field(
                name="Whitelisted Vehicles Roles",
                value="These roles are given to those who are allowed to drive whitelisted cars in your server. They allow users to drive exotics in-game without any alerts.",
                inline=False,
            )
            .add_field(
                name="Whitelisted Vehicle Alert Channel",
                value="This channel is where alerts are sent for staff if someone ignores the in-game message about using an exotic car more than 3 times.",
                inline=False,
            )
            .add_field(
                name="Whitelisted Vehicles",
                value="These are the vehicles that are whitelisted for use in your server. If a user is not in the whitelisted roles, they will be alerted if they use these vehicles in-game.",
                inline=False,
            )
            .add_field(
                name="Alert Message",
                value="This is the message that is sent to the roblox player if they are caught using a whitelisted vehicle without the correct roles.",
                inline=False,
            )
            .add_field(
                name="Current Roles",
                value=(
                    ", ".join([f"<@&{i}>" for i in vehicle_restrictions_roles])
                    if vehicle_restrictions_roles
                    else "None"
                ),
            )
            .add_field(
                name="Current Channel",
                value=(
                    f"<#{vehicle_restrictions_channel}>"
                    if vehicle_restrictions_channel
                    else "None"
                ),
            )
            .add_field(
                name="Current Whitelisted Vehicles",
                value=(
                    ", ".join(vehicle_restrictions_cars)
                    if vehicle_restrictions_cars
                    else "None"
                ),
            )
            .add_field(
                name="Alert Message",
                value=alert_message if alert_message else "None",
            )
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="ER:LC Statistics", row=2, disabled=False)
    async def erlc_statistics(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        view = ERLCStats(self.bot, interaction.user.id, interaction.guild.id)
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        if not sett:
            return
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        try:
            statistics = sett.get("ERLC", {}).get("statistics", {})
        except KeyError:
            statistics = {}

        embed = discord.Embed(
            title="ER:LC Statistics", description="", color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        if statistics.items not in [None, {}]:
            for key, value in statistics.items():
                embed.description += f"**Channel:** <#{key}>\n> **Format:** `{value.get('format', 'None')}`\n"
        else:
            embed.description = "No Statistics Channels Set"
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Automatic Discord Checks", row=2)
    async def automatic_discord_checks(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        view = ERLCDiscordChecksConfiguration(self.bot, interaction.user.id, sett)
        if not sett:
            return

        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        discord_checks = sett.get("ERLC", {}).get("discord_checks", {})
        embed = discord.Embed(
            title="Automatic Discord Checks",
            color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )

        embed.description = (
            "**What is Automatic Discord Checks?** This feature allows you to automatically check if players are in your Discord server when they join your ER:LC server. If they are not, they will be alerted in-game and can be kicked if configured.\n\n" \
            "**Alert Channel:** This is the channel where alerts will be sent if a user fails the Discord checks.\n\n" \
            "**Alert Message:** This is the message that will be sent to the user if they are not in the Discord server.\n\n" \
            "**Maximum Warnings:** After a certain amount of warnings, the user will be kicked from the server.\n\n"
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @discord.ui.button(label="Permission Sync", row=2)
    async def permission_sync(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return

        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        view = ERLCPermissionSync(self.bot, interaction.user.id, sett)
        if not sett:
            return

        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        discord_checks = sett.get("ERLC", {}).get("permission_sync", {})
        embed = discord.Embed(
            title="Permission Sync",
            description="**What is Permission Sync?** This feature automatically gives users the Server Moderator and Server Administrator permissions when they go on shift, removing it when they go off shift.",
            color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        embed.description += "\n\n**Server Moderator Roles:** When these roles go on-duty, they will be given the Server Moderator permission in-game. When they go off-duty, the permissions they were given will be removed. This means that moderators only have staff permissions when they are on-duty, and they don't have access to commands when they are roleplaying."
        embed.description += "\n\n**Server Administrator Roles:** When these roles go on-duty, they will be given the Server Administrator permission in-game. When they go off-duty, the permissions they were given will be removed. This means that administrators only have staff permissions when they are on-duty, and they don't have access to commands when they are roleplaying."

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


    # @discord.ui.button(label="Whitelist Callsign Checks", row=2)
    # async def whitelist_callsign_checks(
    #     self, interaction: discord.Interaction, button: discord.Button
    # ):
    #     val = await self.interaction_check(interaction)
    #     if val is False:
    #         return

    #     sett = await self.bot.settings.find_by_id(interaction.guild.id)
    #     embed = discord.Embed(
    #         title="Whitelist Callsign Checks",
    #         description="This module allows for whitelisting callsign checks in your server. If a player fails the callsign check, they will be alerted in-game.",
    #         color=BLANK_COLOR
    #     )
    #     view = callSignCheck(self.bot, interaction.user.id, sett)
    #     await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ExtendedPriorityConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.button(label="Set Minimum Players", row=3)
    async def set_min_players(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        self.modal = CustomModal(
            "Minimum Players",
            [
                (
                    "min_players",
                    discord.ui.TextInput(
                        label="Minimum Players for a Priority",
                        placeholder="i.e. 5",
                        default=priority_settings.get("min_players", 0) or 0,
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        min_players = self.modal.min_players.value
        min_players = int(min_players.strip())

        priority_settings["min_players"] = min_players
        await func(priority_settings)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Priority Request minimum players has been set to {min_players}.",
        )

    @discord.ui.button(label="Set Maximum Players", row=3)
    async def set_max_players(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        self.modal = CustomModal(
            "Maximum Players",
            [
                (
                    "max_players",
                    discord.ui.TextInput(
                        label="Maximum Players for a Priority",
                        placeholder="i.e. 5",
                        default=priority_settings.get("max_players", 0) or 0,
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        max_players = self.modal.max_players.value
        max_players = int(max_players.strip())

        priority_settings["max_players"] = max_players
        await func(priority_settings)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Priority Request maximum players has been set to {max_players}.",
        )

    @discord.ui.button(label="Set Global Cooldown", row=3)
    async def set_global_cooldown(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        self.modal = CustomModal(
            "Global Cooldown",
            [
                (
                    "global_cooldown",
                    discord.ui.TextInput(
                        label="Global Cooldown (minutes)",
                        placeholder="i.e. 5",
                        default=priority_settings.get("global_cooldown", 0) or 0,
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        global_cooldown = self.modal.global_cooldown.value
        global_cooldown = int(global_cooldown.strip())

        priority_settings["global_cooldown"] = global_cooldown
        await func(priority_settings)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Priority Request global cooldown has been set to {global_cooldown}.",
        )


class PriorityRequestConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        min_values=1,
        max_values=25,
        placeholder="Blacklisted Roles",
        row=0,
    )
    async def blacklisted_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        priority_settings["blacklisted_roles"] = [str(i.id) for i in select.values]
        await func(priority_settings)
        await interaction.response.defer()

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        min_values=1,
        max_values=25,
        placeholder="Mentioned Roles",
        row=1,
    )
    async def mentioned_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        await interaction.response.defer()
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        priority_settings["mentioned_roles"] = [str(i.id) for i in select.values]
        await func(priority_settings)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        min_values=1,
        max_values=1,
        placeholder="Priority Channel",
        row=2,
    )
    async def priority_channel(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        priority_settings["channel_id"] = str(select.values[0].id)
        await func(priority_settings)
        await interaction.response.defer()

    @discord.ui.button(label="Set Cooldown", row=3)
    async def set_cooldown(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        whether_to_continue = await self.interaction_check(interaction)
        if whether_to_continue is False:
            return
        priority_settings = await self.bot.priority_settings.db.find_one(
            {"guild_id": str(interaction.guild.id)}
        )
        func = self.bot.priority_settings.update_by_id
        if not priority_settings:
            priority_settings = {"guild_id": str(interaction.guild.id)}
            func = self.bot.priority_settings.db.insert_one
        self.modal = CustomModal(
            "Cooldown",
            [
                (
                    "cooldown",
                    discord.ui.TextInput(
                        label="Priority Request Cooldown (minutes)",
                        placeholder="i.e. 5",
                        default=priority_settings.get("cooldown", 0) or 0,
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        
        cooldown = self.modal.cooldown.value
        cooldown = int(cooldown.strip())

        priority_settings["cooldown"] = cooldown
        await func(priority_settings)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Priority Request cooldown has been set to {cooldown}.",
        )

    @discord.ui.button(label="More Options", row=3)
    async def more_options(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return
        new_view = ExtendedPriorityConfiguration(self.bot, interaction.user.id, [])
        await interaction.response.send_message(view=new_view, ephemeral=True)



class ExtendedGameLogging(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Message Logging Channel",
        row=0,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def message_logging_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_logging"):
            sett["game_logging"] = {"message": {}}
        if not sett.get("game_logging", {}).get("message"):
            sett["game_logging"]["message"] = {}
        sett["game_logging"]["message"]["channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Message Logging Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="STS Logging Channel",
        row=1,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def sts_logging_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_logging"):
            sett["game_logging"] = {"sts": {}}
        if not sett.get("game_logging", {}).get("sts"):
            sett["game_logging"]["sts"] = {}
        sett["game_logging"]["sts"]["channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"STS Logging Channel Set: <#{select.values[0].id}>",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Priority Logging Channel",
        row=2,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def priority_logging_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_logging"):
            sett["game_logging"] = {"priority": {}}
        if not sett.get("game_logging", {}).get("priority"):
            sett["game_logging"]["priority"] = {}
        sett["game_logging"]["priority"]["channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Priority Logging Channel Set: <#{select.values[0].id}>",
        )


class AntipingConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        placeholder="Anti-Ping",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled", value="enabled", description="Anti-Ping is enabled."
            ),
            discord.SelectOption(
                label="Disabled", value="disabled", description="Anti-Ping is disabled."
            ),
        ],
        max_values=1,
    )
    async def antiping_enabled(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("antiping"):
            sett["antiping"] = {}

        sett["antiping"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Anti-Ping {select.values[0]}.",
        )
        for i in select.options:
            i.default = False

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Affected Roles",
        row=1,
        max_values=5,
        min_values=0,
    )
    async def affected_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("antiping"):
            sett["antiping"] = {"enabled": False, "role": [], "bypass_role": []}
        sett["antiping"]["role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Anti Ping Affected Roles: {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Bypass Roles",
        row=2,
        max_values=5,
        min_values=0,
    )
    async def bypass_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("antiping"):
            sett["antiping"] = {"enabled": False, "role": [], "bypass_role": []}
        sett["antiping"]["bypass_role"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Anti Ping Bypass Roles: {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        placeholder="Use Hierarchy",
        row=3,
        options=[
            discord.SelectOption(
                label="Enabled", value="enabled", description="Hierarchy is enabled."
            ),
            discord.SelectOption(
                label="Disabled", value="disabled", description="Hierarchy is disabled."
            ),
        ],
        max_values=1,
    )
    async def hierarchy_enabled(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("antiping"):
            sett["antiping"] = {
                "enabled": False,
                "role": [],
                "bypass_role": [],
                "use_hierarchy": None,
            }

        sett["antiping"]["use_hierarchy"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Anti Ping Hierarchy {select.values[0]}",
        )
        for i in select.options:
            i.default = False


class GameLoggingConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        placeholder="Message Logging",
        row=0,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="Message Logging is enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="Message Logging is disabled.",
            ),
        ],
        max_values=1,
    )
    async def message_logging_enabled(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_logging"):
            sett["game_logging"] = {"message": {}}
        if not sett.get("game_logging", {}).get("message"):
            sett["game_logging"]["message"] = {}

        sett["game_logging"]["message"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Message Logging {select.values[0]}",
        )
        for i in select.options:
            i.default = False

    @discord.ui.select(
        placeholder="STS Logging",
        row=1,
        options=[
            discord.SelectOption(
                label="Enabled", value="enabled", description="STS Logging is enabled."
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="STS Logging is disabled.",
            ),
        ],
        max_values=1,
    )
    async def sts_logging_enabled(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_logging"):
            sett["game_logging"] = {"sts": {}}
        if not sett.get("game_logging", {}).get("sts"):
            sett["game_logging"]["sts"] = {}

        sett["game_logging"]["sts"]["enabled"] = bool(select.values[0] == "enabled")
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"STS Logging {select.values[0]}",
        )
        for i in select.options:
            i.default = False

    @discord.ui.select(
        placeholder="Priority Logging",
        row=2,
        options=[
            discord.SelectOption(
                label="Enabled",
                value="enabled",
                description="Priority Logging is enabled.",
            ),
            discord.SelectOption(
                label="Disabled",
                value="disabled",
                description="Priority Logging is disabled.",
            ),
        ],
        max_values=1,
    )
    async def priority_logging_enabled(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("game_logging"):
            sett["game_logging"] = {"priority": {}}
        if not sett.get("game_logging", {}).get("priority"):
            sett["game_logging"]["priority"] = {}

        sett["game_logging"]["priority"]["enabled"] = bool(
            select.values[0] == "enabled"
        )
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"Priority Logging {select.values[0]}",
        )
        for i in select.options:
            i.default = False

    @discord.ui.button(label="More Options", row=3)
    async def more_options(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        val = await self.interaction_check(interaction)
        if val is False:
            return
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        new_view = ExtendedGameLogging(
            self.bot,
            interaction.user.id,
            [
                (
                    "Priority Logging Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("game_logging", {})
                            .get("priority", {})
                            .get("channel", 0),
                        )
                    ],
                ),
                (
                    "Message Logging Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("game_logging", {})
                            .get("message", {})
                            .get("channel", 0),
                        )
                    ],
                ),
                (
                    "STS Logging Channel",
                    [
                        discord.utils.get(
                            interaction.guild.channels,
                            id=sett.get("game_logging", {})
                            .get("sts", {})
                            .get("channel", 0),
                        )
                    ],
                ),
            ],
        )
        await interaction.response.send_message(view=new_view, ephemeral=True)


class RDMERLCConfiguration(AssociationConfigurationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="RDM Mentionables",
        row=0,
        max_values=25,
        min_values=0,
    )
    async def rdm_mentionables(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["rdm_mentionables"] = [i.id for i in select.values]
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"RDM Mentionables Set: {', '.join([f'<@&{i.id}>' for i in select.values])}.",
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="RDM Alert Channel",
        row=1,
        max_values=1,
        min_values=0,
        channel_types=[discord.ChannelType.text],
    )
    async def rdm_alert_channel(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        await interaction.response.defer()
        guild_id = interaction.guild.id

        bot = self.bot
        sett = await bot.settings.find_by_id(guild_id)
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["rdm_channel"] = int(select.values[0].id or 0)
        await bot.settings.update_by_id(sett)
        await config_change_log(
            self.bot,
            interaction.guild,
            interaction.user,
            f"RDM Alert Channel Set: <#{select.values[0].id}>",
        )

class ActivityNoticeManagement(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(
        label="Erase Pending Requests", style=discord.ButtonStyle.danger, row=0
    )
    async def erase_pending_requests(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased Pending Requests",
                description="All pending activity notice requests have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        async for item in self.bot.loas.db.find(
            {
                "guild_id": interaction.guild.id,
                "accepted": False,
                "denied": False,
                "voided": False,
            }
        ):
            await self.bot.loas.delete_by_id(item["_id"])

    @discord.ui.button(
        label="Erase LOA Notices", style=discord.ButtonStyle.danger, row=1
    )
    async def erase_loa_notices(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased LOA Notices",
                description="All LOA notices have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        async for item in self.bot.loas.db.find(
            {"guild_id": interaction.guild.id, "type": "LOA", "accepted": True}
        ):
            await self.bot.loas.delete_by_id(item["_id"])

    @discord.ui.button(
        label="Erase RA Notices", style=discord.ButtonStyle.danger, row=2
    )
    async def erase_ra_notices(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased RA Notices",
                description="All RA notices have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        async for item in self.bot.loas.db.find(
            {"guild_id": interaction.guild.id, "type": "RA", "accepted": True}
        ):
            await self.bot.loas.delete_by_id(item["_id"])


class PunishmentManagement(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(
        label="Erase All Punishments", style=discord.ButtonStyle.danger, row=0
    )
    async def erase_all_punishments(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased All Punishments",
                description="All punishments have been deleted.\n*This may take up to 10 minutes to fully delete all of your punishments.*",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        await self.bot.punishments.remove_warnings_by_spec(
            guild_id=interaction.guild.id
        )

    @discord.ui.button(
        label="Erase Punishments By Type", style=discord.ButtonStyle.danger, row=1
    )
    async def erase_type_punishments(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        modal = CustomModal(
            "Punishment Type",
            [
                (
                    "punishment_type",
                    discord.ui.TextInput(
                        label="Punishment Type", placeholder="This is case-sensitive."
                    ),
                )
            ],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        sustained_interaction = modal.interaction

        count = await self.bot.punishments.db.count_documents(
            {"Guild": interaction.guild.id, "Type": modal.punishment_type.value}
        )
        if count == 0:
            return await sustained_interaction.followup.send(
                embed=discord.Embed(
                    title="Not Found",
                    description="There are no punishments with this type.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        await sustained_interaction.followup.send(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased Punishments",
                description=f"All punishments of **{modal.punishment_type.value}** have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        await self.bot.punishments.remove_warnings_by_spec(
            guild_id=interaction.guild.id, warning_type=modal.punishment_type.value
        )

    @discord.ui.button(
        label="Erase Punishments By Username", style=discord.ButtonStyle.danger, row=2
    )
    async def erase_username_punishments(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        modal = CustomModal(
            "Punishment Type",
            [
                (
                    "username",
                    discord.ui.TextInput(
                        label="ROBLOX Username", placeholder="This is case-sensitive."
                    ),
                )
            ],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        sustained_interaction = modal.interaction

        try:
            roblox_client = roblox.Client()
            roblox_player = await roblox_client.get_user_by_username(
                modal.username.value
            )
        except roblox.UserNotFound:
            return await sustained_interaction.followup.send(
                embed=discord.Embed(
                    title="Not Found",
                    description="There are no punishments associated to this username.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        count = await self.bot.punishments.db.count_documents(
            {"Guild": interaction.guild.id, "UserID": roblox_player.id}
        )
        if count == 0:
            return await sustained_interaction.followup.send(
                embed=discord.Embed(
                    title="Not Found",
                    description="There are no punishments associated to this username.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        await sustained_interaction.followup.send(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased Punishments",
                description=f"All punishments of **{roblox_player.name}** have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        await self.bot.punishments.remove_warnings_by_spec(
            guild_id=interaction.guild.id, user_id=roblox_player.id
        )


class ShiftLoggingManagement(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(
        label="Erase All Shifts", style=discord.ButtonStyle.danger, row=0
    )
    async def erase_all_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased All Shifts",
                description="All shifts have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        active_shift_users = []
        async for shift in self.bot.shift_management.shifts.db.find(
            {"Guild": interaction.guild.id, "EndEpoch": 0}
        ):
            user_id = shift["UserID"]
            member = interaction.guild.get_member(user_id) or await interaction.guild.fetch_member(user_id)
            if member and member not in active_shift_users:
                active_shift_users.append(member)

        async for item in self.bot.shift_management.shifts.db.find(
            {"Guild": interaction.guild.id}
        ):
            await self.bot.shift_management.shifts.delete_by_id(item["_id"])

        for member in active_shift_users:
            try:
                await member.send(
                    embed=discord.Embed(
                        title="Shift Termination Notice",
                        description=f"Your active shift has been terminated due to a shift wipe in {interaction.guild.name}.",
                        color=discord.Color.red(),
                    )
                )
            except discord.Forbidden:
                print(f"Could not send DM to {member.name}")

    @discord.ui.button(
        label="Erase Past Shifts", style=discord.ButtonStyle.danger, row=1
    )
    async def erase_past_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased Past Shifts",
                description="All past shifts have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        async for item in self.bot.shift_management.shifts.db.find(
            {"Guild": interaction.guild.id, "EndEpoch": {"$ne": 0}}
        ):
            await self.bot.shift_management.shifts.delete_by_id(item["_id"])

    @discord.ui.button(
        label="Erase Active Shifts", style=discord.ButtonStyle.danger, row=2
    )
    async def erase_active_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased Active Shifts",
                description="All active shifts have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        async for item in self.bot.shift_management.shifts.db.find(
            {"Guild": interaction.guild.id, "EndEpoch": {"$eq": 0}}
        ):
            await self.bot.shift_management.shifts.delete_by_id(item["_id"])

    @discord.ui.button(
        label="Erase Shifts By Type", style=discord.ButtonStyle.danger, row=3
    )
    async def erase_type_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        modal = CustomModal(
            "Shift Type",
            [
                (
                    "shift_type",
                    discord.ui.TextInput(
                        label="Shift Type", placeholder="This is case-sensitive."
                    ),
                )
            ],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        sustained_interaction = modal.interaction

        count = await self.bot.shift_management.shifts.db.count_documents(
            {"Guild": interaction.guild.id, "Type": modal.shift_type.value}
        )
        if count == 0:
            return await sustained_interaction.followup.send(
                embed=discord.Embed(
                    title="Not Found",
                    description="There are no shifts with this type.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        await sustained_interaction.followup.send(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Erased Shifts",
                description=f"All shifts of **{modal.shift_type.value}** have been deleted.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

        await self.bot.shift_management.shifts.db.delete_many(
            {"Guild": interaction.guild.id, "Type": modal.shift_type.value}
        )



class ERLCDiscordChecksConfiguration(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, sett: dict):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.sett = sett
        self.user_id = user_id
        
        self.discord_checks = sett.get("ERLC", {}).get("discord_checks", {})
        enabled = self.discord_checks.get("enabled", False)
        channel_id = self.discord_checks.get("channel_id")
        kick_after = self.discord_checks.get("kick_after", 0)
        
        self._setup_components(enabled, channel_id, kick_after)
    
    def _setup_components(self, enabled: bool, channel_id: int, kick_after: int):
        self.enable_button = discord.ui.Select(
            placeholder="Automatic Discord Checks",
            options=[
                discord.SelectOption(label="Enabled", value="enabled", default=enabled),
                discord.SelectOption(label="Disabled", value="disabled", default=not enabled),
            ],
            row=0,
            max_values=1,
        )
        self.enable_button.callback = self.enable_button_callback
        self.add_item(self.enable_button)

        default_values = [discord.Object(id=channel_id)] if channel_id else None
        self.alert_channel_select = discord.ui.ChannelSelect(
            placeholder="Select Alert Channel",
            channel_types=[discord.ChannelType.text],
            default_values=default_values,
            row=1,
            max_values=1,
        )
        self.alert_channel_select.callback = self.alert_channel_select_callback
        self.add_item(self.alert_channel_select)

        self.kick_after = discord.ui.Select(
            placeholder="Kick After",
            options=[
                discord.SelectOption(
                    label="No Kick",
                    value=str(0),
                    default=(kick_after == 0)
                )
            ] + [
                discord.SelectOption(
                    label=f"{i} warning{'s' if i > 1 else ''}", 
                    value=str(i),
                    default=(i == kick_after)
                ) for i in range(1, 11)
            ],
            row=2,
        )
        self.kick_after.callback = self.kick_after_callback
        self.add_item(self.kick_after)

        self.alert_message = discord.ui.Button(
            label="Set Alert Message", 
            style=discord.ButtonStyle.secondary,
            row=3
        )
        self.alert_message.callback = self.alert_message_callback
        self.add_item(self.alert_message)

    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to interact with this view"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return False
        return True
    
    async def _ensure_settings_structure(self, sett: dict) -> None:
        """Ensure the nested dictionary structure exists"""
        if "ERLC" not in sett:
            sett["ERLC"] = {}
        if "discord_checks" not in sett["ERLC"]:
            sett["ERLC"]["discord_checks"] = {"enabled": False}
    
    async def _update_settings_and_log(self, interaction: discord.Interaction, sett: dict, message: str) -> None:
        """Update settings and log the change"""
        await self.bot.settings.update_by_id(sett)
        await config_change_log(self.bot, interaction.guild, interaction.user, message)
    
    async def _update_embed_field(self, interaction: discord.Interaction, field_index: int, name: str, value: str) -> None:
        """Update a specific field in the embed"""
        embed = interaction.message.embeds[0]
        embed.set_field_at(field_index, name=name, value=value, inline=False)
        await interaction.edit_original_response(embed=embed, view=self)

    async def enable_button_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        
        enabled = self.enable_button.values[0] == "enabled"
        sett["ERLC"]["discord_checks"]["enabled"] = enabled
        
        if enabled and "channel_id" not in sett["ERLC"]["discord_checks"]:
            sett["ERLC"]["discord_checks"]["channel_id"] = None
        
        await self._update_settings_and_log(
            interaction, sett, 
            f"Discord Checks have been {'enabled' if enabled else 'disabled'}."
        )

        for option in self.enable_button.options:
            option.default = False
        
        await self._update_embed_field(
            interaction, 0, 
            "Enabled/Disabled Discord Checks", 
            f"**Current Status:** {'Enabled' if enabled else 'Disabled'}"
        )

    async def alert_channel_select_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        
        channel_id = self.alert_channel_select.values[0].id if self.alert_channel_select.values else None
        sett["ERLC"]["discord_checks"]["channel_id"] = channel_id
        
        await self._update_settings_and_log(
            interaction, sett,
            f"Discord Checks Channel has been set to <#{channel_id}>."
        )
        
        await self._update_embed_field(
            interaction, 1,
            "Discord Check Channel",
            f"**Current Channel:** <#{channel_id}>"
        )

    async def kick_after_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        
        kick_after = int(self.kick_after.values[0]) if self.kick_after.values else 4
        sett["ERLC"]["discord_checks"]["kick_after"] = kick_after
        
        await self._update_settings_and_log(
            interaction, sett,
            f"Discord Checks Kick After has been set to {kick_after} warnings."
        )
        
        await self._update_embed_field(
            interaction, 2,
            "Kick After",
            f"**Current Duration:** {kick_after} warning{'s' if kick_after > 1 else ''}"
        )

    async def alert_message_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return

        modal = CustomModal(
            "Alert Message Configuration",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Alert Message",
                        default=self.discord_checks.get("message", ""),
                        required=True,
                        max_length=500,
                        style=discord.TextStyle.long,
                    )
                )
            ],
        )
        
        await interaction.response.send_modal(modal)
        
        if await modal.wait():
            return

        alert_message = modal.value.value
        if not alert_message:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Alert Message Provided",
                    description="You must provide an alert message.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        sett["ERLC"]["discord_checks"]["message"] = alert_message
        
        await self._update_settings_and_log(
            interaction, sett,
            f"Discord Checks Alert Message has been set to: {alert_message}"
        )

        await interaction.followup.send(
            embed=discord.Embed(
                title="Alert Message Set",
                description=f"Your alert message has been set to: {alert_message}",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        
        # Update the embed
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name="Alert Message", value=f"**Current Message:** {alert_message}", inline=False)
        await interaction.edit_original_response(embed=embed, view=self)


class ERLCPermissionSync(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, sett: dict):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.sett = sett
        self.user_id = user_id
        
        self.permission_sync = sett.get("ERLC", {}).get("permission_sync", {})
        enabled = self.permission_sync.get("enabled", False)
        mod_roles = self.permission_sync.get("moderator_roles", [])
        admin_roles = self.permission_sync.get("administrator_roles", [])

        self._setup_components(enabled, mod_roles, admin_roles)
    
    def _setup_components(self, enabled: bool, mod_roles: list[int], admin_roles: list[int]):
        self.enable_button = discord.ui.Select(
            placeholder="Permission Sync",
            options=[
                discord.SelectOption(label="Enabled", value="enabled", default=enabled),
                discord.SelectOption(label="Disabled", value="disabled", default=not enabled),
            ],
            row=0,
            max_values=1,
        )
        self.enable_button.callback = self.enable_button_callback
        self.add_item(self.enable_button)

        default_values = [discord.Object(id=role_id) for role_id in mod_roles] if mod_roles else None
        self.mod_roles_select = discord.ui.RoleSelect(
            placeholder="Server Moderator Roles",
            default_values=default_values,
            row=1,
            max_values=25,
        )
        self.mod_roles_select.callback = self.mod_roles_select_callback
        self.add_item(self.mod_roles_select)

        default_values = [discord.Object(id=role_id) for role_id in admin_roles] if admin_roles else None
        self.admin_roles_select = discord.ui.RoleSelect(
            placeholder="Server Administrator Roles",
            default_values=default_values,
            row=2,
            max_values=25,
        )
        self.admin_roles_select.callback = self.admin_roles_select_callback
        self.add_item(self.admin_roles_select)

        
    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return False
        return True
    
    async def _update_settings_and_log(self, interaction: discord.Interaction, sett: dict, message: str) -> None:
        await self.bot.settings.update_by_id(sett)
        await config_change_log(self.bot, interaction.guild, interaction.user, message)
    
    async def enable_button_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)        
        enabled = self.enable_button.values[0] == "enabled"
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        if "permission_sync" not in sett["ERLC"]:
            sett["ERLC"]["permission_sync"] = {"enabled": False, "moderator_roles": [], "administrator_roles": []}
        sett["ERLC"]["permission_sync"]["enabled"] = enabled
        
        await self._update_settings_and_log(
            interaction, sett, 
            f"Permission Sync has been {'enabled' if enabled else 'disabled'}."
        )
        
    async def mod_roles_select_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        
        mod_roles = [role.id for role in self.mod_roles_select.values]
        if "ERLC" not in sett:
            sett["ERLC"] = {}
        if "permission_sync" not in sett["ERLC"]:
            sett["ERLC"]["permission_sync"] = {"enabled": False, "moderator_roles": [], "administrator_roles": []}
        sett["ERLC"]["permission_sync"]["moderator_roles"] = mod_roles
        

    async def admin_roles_select_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)

        administrator_roles = [role.id for role in self.admin_roles_select.values]
        if "ERLC" not in sett:
            sett["ERLC"] = {}
        if "permission_sync" not in sett["ERLC"]:
            sett["ERLC"]["permission_sync"] = {"enabled": False, "moderator_roles": [], "administrator_roles": []}
        sett["ERLC"]["permission_sync"]["administrator_roles"] = administrator_roles

