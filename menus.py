import asyncio
import datetime

import typing
import discord
import pytz
from discord import Interaction
from discord.ext import commands
from bson import ObjectId
from datamodels.ShiftManagement import ShiftItem
from utils.constants import (
    blank_color,
    BLANK_COLOR,
    GREEN_COLOR,
    ORANGE_COLOR,
    RED_COLOR,
)
from utils.timestamp import td_format
from utils.utils import (
    
    int_failure_embed,
    int_pending_embed,
    time_converter,
    get_elapsed_time,
    generalised_interaction_check_failure,
    generator,
    ArgumentMockingInstance,
    config_change_log,
    admin_check,
)
import gspread
import random


REQUIREMENTS = ["gspread", "oauth2client"]



class ShiftModificationDropdown(discord.ui.Select):
    def __init__(self, user_id, other=False):
        self.user_id = user_id
        if other is False:
            options = [
                discord.SelectOption(
                    label="On Duty",
                    value="on",
                    description="Start your in-game shift",
                ),
                discord.SelectOption(
                    label="Toggle Break",
                    value="break",
                    description="Taking a break? Toggle your break status",
                ),
                discord.SelectOption(
                    label="Off Duty",
                    value="off",
                    description="End your in-game shift",
                ),
                discord.SelectOption(
                    label="Void shift",
                    value="void",
                    description="Void your in-game shift. This is irreversible.",
                ),
            ]
        else:
            options = [
                discord.SelectOption(
                    label="On Duty",
                    value="on",
                    description="Start their in-game shift",
                ),
                discord.SelectOption(
                    label="Toggle Break",
                    value="break",
                    description="Taking a break? Toggle their break status",
                ),
                discord.SelectOption(
                    label="Off Duty",
                    value="off",
                    description="End their in-game shift",
                ),
            ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.value = self.values[0]
            self.disabled = True
            for option in self.options:
                if option.value == self.values[0]:
                    option.default = True

            await interaction.message.edit(view=self.view)
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)


class AdministrativeActionsDropdown(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label="Add time",
                value="add",
                description="Add time to their current shift",
            ),
            discord.SelectOption(
                label="Remove time",
                value="remove",
                description="Remove time from their current shift",
            ),
            discord.SelectOption(
                label="Void shift",
                value="void",
                description="Void their shift, and remove it from the leaderboard",
            ),
            discord.SelectOption(
                label="Clear Member Shifts",
                value="clear",
                description="Clear all of their shifts from the leaderboard",
            ),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Administrative Actions",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.admin_value = self.values[0]
            self.disabled = True
            for option in self.options:
                if option.value == self.values[0]:
                    option.default = True

            for item in self.view.children:
                if isinstance(item, discord.ui.Select):
                    if item is not self:
                        item.disabled = True

            await interaction.message.edit(view=self.view)
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)



class MultiPaginatorDropdown(discord.ui.Select):
    def __init__(self, user_id, options: list, pages: dict, limit=1):
        self.user_id = user_id
        self.pages = pages
        optionList = []

        for option in options:
            if isinstance(option, str):
                optionList.append(
                    discord.SelectOption(
                        label=option.replace("_", " ").title(), value=option
                    )
                )
            elif isinstance(option, discord.SelectOption):
                optionList.append(option)

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option",
            min_values=1,
            max_values=limit,
            options=optionList,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            await interaction.message.edit(
                content=f"<:ERMCheck:1111089850720976906>  **{interaction.user.name},** you're currently viewing the **{self.values[0].replace('_', ' ').title()}** commands!",
                embed=self.pages.get(self.values[0]),
            )
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return


# noinspection PyUnresolvedReferences
class MultiDropdown(discord.ui.Select):
    def __init__(self, user_id, options: list):
        self.user_id = user_id
        optionList = []

        for option in options:
            if isinstance(option, str):
                optionList.append(
                    discord.SelectOption(
                        label=option.replace("_", " ").title(), value=option
                    )
                )
            elif isinstance(option, discord.SelectOption):
                optionList.append(option)

        # # # # print(t(t(t(t(optionList)

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option",
            max_values=len(optionList),
            options=optionList,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            if len(self.values) == 1:
                self.view.value = self.values[0]
            else:
                self.view.value = self.values
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return




class ModificationSelectMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.00)
        self.value = None
        self.user_id = user_id

        self.add_item(ShiftModificationDropdown(self.user_id))


class AdministrativeSelectMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.00)
        self.value = None
        self.admin_value = None
        self.user_id = user_id

        self.add_item(ShiftModificationDropdown(self.user_id, other=True))
        self.add_item(AdministrativeActionsDropdown(self.user_id))


class YesNoMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = True
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = False
        await interaction.edit_original_response(view=self)
        self.stop()


class AcknowledgeMenu(discord.ui.View):
    def __init__(self, user_id, note: str):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        if note:
            for child in self.children:
                if child.label == "NOTE":
                    child.label = note

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(
        label="I acknowledge and understand", style=discord.ButtonStyle.green
    )
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = True
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(
        label="NOTE", style=discord.ButtonStyle.secondary, row=1, disabled=True
    )
    async def note(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


class YesNoExpandedMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Yes, continue", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = True
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(
        label="I'll do this another time", style=discord.ButtonStyle.secondary
    )
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = False
        await interaction.edit_original_response(view=self)
        self.stop()


class YesNoColourMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = True
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return

        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = False
        await interaction.edit_original_response(view=self)
        self.stop()


class ColouredButton(discord.ui.Button):
    def __init__(self, user_id, label, style, emoji=None):
        super().__init__(label=label, style=style, emoji=emoji)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.value = self.label
            self.view.stop()
        else:
            await generalised_interaction_check_failure(interaction.response)
            return


class CustomExecutionButton(discord.ui.Button):
    def __init__(self, user_id, label, style, emoji=None, func=None, row=0, disabled=False):
        """

        A button used for custom execution functions. This is often used to subvert pagination limitations.

        :param user_id: the user who can use this button
        :param label: the label of the button
        :param style: style of the button : discord.ButtonStyle
        :param emoji: emoji of the button
        :param func: function to be executed when pressed
        """

        super().__init__(label=label, style=style, emoji=emoji, row=row, disabled=disabled)
        self.func = func
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await self.func(interaction, self)
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )


class ColouredMenu(discord.ui.View):
    def __init__(self, user_id, buttons: list[str]):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        for index, button in enumerate(buttons):
            if index == 0:
                self.add_item(
                    ColouredButton(
                        self.user_id, button, discord.ButtonStyle.primary, emoji=None
                    )
                )
            else:
                self.add_item(
                    ColouredButton(
                        self.user_id, button, discord.ButtonStyle.secondary, emoji=None
                    )
                )


class EnableDisableMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Enable", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = True
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = False
        await interaction.edit_original_response(view=self)
        self.stop()


class LinkPathwayMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="ERM", style=discord.ButtonStyle.secondary)
    async def ERM(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "erm"
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Bloxlink", style=discord.ButtonStyle.danger)
    async def Bloxlink(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "bloxlink"
        await interaction.edit_original_response(view=self)
        self.stop()


class ShiftModify(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Add time (+)", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "add"
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Remove time (-)", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "remove"
        await interaction.edit_original_response(view=self)
        self.stop()

    @discord.ui.button(label="End shift", style=discord.ButtonStyle.danger)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "end"
        await interaction.edit_original_response(view=self)
        self.stop()

    @discord.ui.button(label="Void shift", style=discord.ButtonStyle.danger)
    async def void(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "void"
        await interaction.edit_original_response(view=self)
        self.stop()


class ActivityNoticeModification(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Add time (+)", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "add"
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Remove time (-)", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "remove"
        await interaction.edit_original_response(view=self)
        self.stop()

    @discord.ui.button(label="End Activity Notice", style=discord.ButtonStyle.danger)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "end"
        await interaction.edit_original_response(view=self)
        self.stop()

    @discord.ui.button(label="Void Activity Notice", style=discord.ButtonStyle.danger)
    async def void(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "void"
        await interaction.edit_original_response(view=self)
        self.stop()


class PartialShiftModify(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Add time (+)", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "add"
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Remove time (-)", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "remove"
        await interaction.edit_original_response(view=self)
        self.stop()


class LOAMenu(discord.ui.View):
    def __init__(self, bot, roles, loa_roles, loa_object, user_id, code):

        super().__init__(timeout=None)
        self.value = None
        self.bot = bot
        self.loa_object = loa_object
        if isinstance(roles, list):
            self.roles = roles
        elif isinstance(roles, int):
            self.roles = [roles]
        self.loa_role = loa_roles
        self.user_id = user_id
        self.id = code

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, custom_id="loamenu:accept"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # await interaction.response.defer()
        await interaction.response.defer(ephemeral=True, thinking=True)

        # checking for admin permission as opposed to roles - property kept for legacy
        if not await admin_check(self.bot, interaction.guild, interaction.user):
            await generalised_interaction_check_failure(interaction.followup)
            return

        for item in self.children:
            item.disabled = True
            if item.label == "Accept":
                item.label = "Accepted"
            else:
                self.remove_item(item)
        s_loa = None

        for loa in await self.bot.loas.get_all():
            if (
                loa["message_id"] == interaction.message.id
                and loa["guild_id"] == interaction.guild.id
            ):
                s_loa = loa

        s_loa["accepted"] = True
        guild = self.bot.get_guild(s_loa["guild_id"])
        try:
            user = await guild.fetch_member(s_loa["user_id"])
        except discord.NotFound:
            user = None
        if user is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find member",
                    description="I could not find the staff member which requested this Leave of Absence.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        mentionable = ""
        try:
            await user.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Activity Notice Accepted",
                    description=f"Your {s_loa['type']} request in **{interaction.guild.name}** was accepted!",
                    color=GREEN_COLOR,
                )
            )
        except:
            pass

        try:
            await self.bot.loas.update_by_id(s_loa)
            if isinstance(self.loa_role, int):
                role = [discord.utils.get(guild.roles, id=self.loa_role)]
            elif isinstance(self.loa_role, list):
                role = [
                    discord.utils.get(guild.roles, id=role) for role in self.loa_role
                ]

            for rl in role:
                if rl not in user.roles:
                    await user.add_roles(rl)

            self.value = True
        except discord.HTTPException:
            pass
        embed = interaction.message.embeds[0]
        embed.title = (
            f"{self.bot.emoji_controller.get_emoji('success')} {s_loa['type']} Accepted"
        )
        embed.colour = GREEN_COLOR
        embed.set_footer(text=f"Accepted by {interaction.user.name}")

        await interaction.message.edit(
            embed=embed,
            view=None,
        )

        await self.bot.views.delete_by_id(self.id)
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Request Accepted",
                description=f"You have successfully accepted this staff member's {s_loa['type']} Request.",
                color=GREEN_COLOR,
            )
        )
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        custom_id="loamenu:deny",
    )
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        # checking for admin permission as opposed to roles - property kept for legacy
        if not await admin_check(self.bot, interaction.guild, interaction.user):
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        
        for item in self.children:
            item.disabled = True

        modal = CustomModal(
            f"Reason for Denial",
            [
                (
                    "value",
                    (
                        discord.ui.TextInput(
                            label="Reason for denial",
                            placeholder="Enter a reason for denying this person's request.",
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

        reason = modal.value.value

        for item in self.children:
            item.disabled = True
            if item.label == button.label:
                item.label = "Denied"
            else:
                self.remove_item(item)
        s_loa = None

        async for loa_item in self.bot.loas.db.find(
            {"guild_id": interaction.guild.id, "message_id": interaction.message.id}
        ):
            s_loa = loa_item

        if not s_loa:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find LOA",
                    description="I could not find the activity notice associated with this menu.",
                ),
                ephemeral=True,
            )

        s_loa["denied"] = True
        s_loa["denial_reason"] = reason

        user = interaction.guild.get_member(s_loa["user_id"])
        if not user:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find member",
                    description="I could not find the staff member who made this request.",
                ),
                ephemeral=True,
            )

        try:
            await user.send(
                embed=discord.Embed(
                    title="Activity Notice Denied",
                    description=f"Your {s_loa['type']} request in **{interaction.guild.name}** was denied.\n**Reason:** {reason}",
                    color=BLANK_COLOR,
                )
            )
        except:
            pass
        await self.bot.loas.update_by_id(s_loa)

        embed = interaction.message.embeds[0]
        embed.title = f"{s_loa['type']} Denied"
        embed.colour = BLANK_COLOR
        embed.set_footer(text=f"Denied by {interaction.user.name}")

        await interaction.message.edit(embed=embed, view=None)
        self.value = False
        await self.bot.views.delete_by_id(self.id)

        self.stop()


class AddReminder(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    @discord.ui.button(label="Create a reminder", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            self.value = "create"
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)


class ManageReminders(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.modal: typing.Union[None, CustomModal] = None

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Create a reminder",
                [
                    (
                        "name",
                        discord.ui.TextInput(
                            label="Name",
                            placeholder="Name of your reminder",
                            required=True,
                        ),
                    ),
                    (
                        "content",
                        discord.ui.TextInput(
                            label="Content",
                            style=discord.TextStyle.long,
                            placeholder="Content of your reminder",
                            required=True,
                        ),
                    ),
                    (
                        "time",
                        discord.ui.TextInput(
                            label="Interval",
                            placeholder="What would you like you like the interval to be? (e.g. 5m)",
                            required=True,
                            style=discord.TextStyle.short,
                        ),
                    ),
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            self.value = "create"
            self.stop()
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Edit a reminder",
                [
                    (
                        "identifier",
                        discord.ui.TextInput(
                            label="ID",
                            placeholder="ID of your reminder",
                            required=True,
                        ),
                    ),
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            self.value = "edit"
            self.stop()
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Pause a reminder",
                [
                    (
                        "id_value",
                        discord.ui.TextInput(
                            label="ID",
                            placeholder="ID of your reminder",
                            required=True,
                        ),
                    ),
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            self.value = "pause"
            self.stop()
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Delete a reminder",
                [
                    (
                        "id_value",
                        discord.ui.TextInput(
                            label="ID",
                            placeholder="ID of your reminder",
                            required=True,
                        ),
                    ),
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            self.value = "delete"
            self.stop()
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )





class CustomisePunishmentType(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.modal: typing.Union[CreatePunishmentType, DeletePunishmentType, None] = (
            None
        )

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            modal = CreatePunishmentType()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            self.value = "create"
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            modal = DeletePunishmentType()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            self.value = "delete"
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

class RemoveReminder(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    @discord.ui.button(label="Delete a reminder", style=discord.ButtonStyle.danger)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            self.value = "delete"
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)




class RemoveWarning(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.bot = bot
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        await interaction.response.defer()
        for item in self.children:
            self.remove_item(item)
        self.value = True

        # success = discord.Embed(
        #     title="<:CheckIcon:1035018951043842088> Removed Punishment",
        #     description="<:ArrowRightW:1035023450592514048>I've successfully removed the punishment from the user.",
        #     color=0x71C15F,
        # )

        # await interaction.edit_original_response(embed=success, view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        await interaction.response.defer()
        for item in self.children:
            self.remove_item(item)
        self.value = False

        # success = discord.Embed(
        #     title="<:ErrorIcon:1035000018165321808> Cancelled",
        #     description="<:ArrowRightW:1035023450592514048>The punishment has not been removed from the user.",
        #     color=0xFF3C3C,
        # )
        #
        # await interaction.edit_original_response(embed=success, view=self)
        self.stop()


class RequestReason(discord.ui.Modal, title="Edit Reason"):
    name = discord.ui.TextInput(label="Reason")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class RequestData(discord.ui.Modal, title="Edit Reason"):
    data = discord.ui.TextInput(label="Reason")

    def __init__(self, title="PLACEHOLDER", label="PLACEHOLDER"):
        self.data.label = label
        super().__init__(title=title)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class CustomModal(discord.ui.Modal, title="Edit Reason"):
    def __init__(self, title, options, epher_args: dict = None):
        super().__init__(title=title)
        if epher_args is None:
            epher_args = {}
        self.saved_items = {}
        self.epher_args = epher_args
        self.interaction = None

        for name, option in options:
            self.add_item(option)
            self.saved_items[name] = option

    async def on_submit(self, interaction: discord.Interaction):
        for key, item in self.saved_items.items():
            setattr(self, key, item)
        self.interaction = interaction
        await interaction.response.defer(**self.epher_args)
        self.stop()


class CreatePunishmentType(discord.ui.Modal, title="Create Punishment Type"):
    name = discord.ui.TextInput(
        label="Name",
        placeholder="e.g. Verbal Warning",
        max_length=20,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stop()


class DeletePunishmentType(discord.ui.Modal, title="Delete Punishment Type"):
    name = discord.ui.TextInput(
        label="Name",
        placeholder="e.g. Verbal Warning",
        max_length=20,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class TimeRequest(discord.ui.Modal, title="Temporary Ban"):
    time = discord.ui.TextInput(label="Time (s/m/h/d)")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class ChangeWarningType(discord.ui.Select):
    def __init__(self, user_id, options: list):
        self.user_id: int = user_id

        selected_options = []
        using_options = False
        for option in options:
            if isinstance(option, str | int):
                option = discord.SelectOption(
                    label=str(option),
                    value=str(option),
                )
                selected_options.append(option)
                using_options = True
            elif isinstance(option, discord.SelectOption):
                option.emoji = "<:MalletWhite:1035258530422341672>"
                selected_options.append(option)
                using_options = True

        if not using_options:
            selected_options = [
                discord.SelectOption(
                    label="Warning",
                    value="Warn",
                    description="A warning, the smallest form of logged punishment",
                ),
                discord.SelectOption(
                    label="Kick",
                    value="Kick",
                    description="Removing a user from the game, usually given after warnings",
                ),
                discord.SelectOption(
                    label="Ban",
                    value="Ban",
                    description="A permanent form of removing a user from the game, given after kicks",
                ),
                discord.SelectOption(
                    label="Temporary Ban",
                    value="Temporary Ban",
                    description="Given after kicks, not enough to warrant a permanent removal",
                ),
                discord.SelectOption(
                    label="BOLO",
                    value="BOLO",
                    description="Cannot be found in the game, be on the lookout",
                ),
            ]
        super().__init__(
            placeholder="Select a warning type",
            min_values=1,
            max_values=1,
            options=selected_options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            if self.values[0] == "Temporary Ban":
                modal = TimeRequest()
                await interaction.response.send_modal(modal)
                seconds = 0
                if modal.time.value.endswith("s", "m", "h", "d"):
                    if modal.time.value.endswith("s"):
                        seconds = int(modal.time.value.removesuffix("s"))
                    elif modal.time.value.endswith("m"):
                        seconds = int(modal.time.value.removesuffix("m")) * 60
                    elif modal.time.value.endswith("h"):
                        seconds = int(modal.time.value.removesuffix("h")) * 60 * 60
                    else:
                        seconds = int(modal.time.value.removesuffix("d")) * 60 * 60 * 24
                else:
                    seconds = int(modal.time.value)
            await interaction.response.defer()
            try:
                self.view.value = [self.values[0], seconds]
            except UnboundLocalError:
                self.view.value = self.values[0]
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)


class EditWarningSelect(discord.ui.Select):
    def __init__(self, user_id: int, inherited_options: list):
        self.user_id: int = user_id
        self.inherited_options = inherited_options

        options = [
            discord.SelectOption(
                label="Edit reason",
                value="edit",
                description="Edit the reason of the punishment",
            ),
            discord.SelectOption(
                label="Change punishment type",
                value="change",
                description="Change the punishment type to a higher or lower severity",
            ),
            discord.SelectOption(
                label="Delete punishment",
                value="delete",
                description="Delete the punishment from the database. This is irreversible.",
            ),
        ]

        super().__init__(
            placeholder="Select an option", min_values=1, max_values=1, options=options
        )

    # This one is similar to the confirmation button except sets the inner value to `False`
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            self.view.value = self.values[0]
            if self.view.value == "edit":
                if interaction.user.id != self.user_id:
                    return
                # await interaction.response.defer()
                for item in self.view.children:
                    item.disabled = True
                self.view.value = "edit"

                self.view.modal = RequestReason()
                await interaction.response.send_modal(self.view.modal)
                await self.view.modal.wait()
                self.view.further_value = self.view.modal.name.value
                self.view.stop()
            elif self.view.value == "change":
                if interaction.user.id != self.user_id:
                    return
                for item in self.view.children:
                    item.disabled = True
                self.value = "type"
                view = WarningDropdownMenu(interaction.user.id, self.inherited_options)
                await interaction.message.edit(
                    content="<:ERMPending:1111097561588183121> **{},** please select a new punishment type.".format(
                        interaction.user.name
                    ),
                    embed=None,
                    view=view,
                )
                await view.wait()
                self.view.further_value = view.value

                self.view.stop()
            elif self.view.value == "delete":
                if interaction.user.id != self.user_id:
                    return
                await interaction.response.defer()
                for item in self.view.children:
                    item.disabled = True
                self.value = "delete"
                await interaction.edit_original_response(view=self.view)
                self.view.stop()
            else:
                await int_failure_embed(interaction, "you have not picked an option.")
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)


class EditWarning(discord.ui.View):
    def __init__(self, bot, user_id, options):
        super().__init__(timeout=600.0)
        self.value: typing.Union[None, str] = None
        self.bot: typing.Union[
            discord.ext.commands.Bot, discord.ext.commands.AutoShardedBot
        ] = bot
        self.user_id: int = user_id
        self.modal: typing.Union[None, discord.ui.Modal] = None
        self.further_value: typing.Union[None, str] = None
        self.options = options
        self.add_item(EditWarningSelect(user_id, options))


class RemoveBOLO(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = True

        await interaction.edit_original_response(
            content=f"<:ERMCheck:1111089850720976906> **{interaction.user.name}**, I've removed the BOLO from that user.",
            view=self,
        )
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = False

        await interaction.edit_original_response(
            content=f"<:ERMCheck:1111089850720976906> **{interaction.user.name}**, sounds good! I won't remove that punishment.",
            view=self,
        )
        self.stop()



class RequestDataView(discord.ui.View):
    def __init__(self, user_id, title: str, label: str):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.modal: typing.Union[None, RequestData] = None
        self.title = title
        self.label = label
        for item in self.children:
            item.label = self.title

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Enter Strike Amount", style=discord.ButtonStyle.secondary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        self.modal = RequestData(self.title, self.label)
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stop()


class CustomModalView(discord.ui.View):
    def __init__(
        self,
        user_id,
        title: str,
        label: str,
        options: typing.List[typing.Tuple[str, discord.ui.TextInput]],
        epher_args: typing.Optional[dict] = None,
    ):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.modal: typing.Union[None, CustomModal] = None
        self.title = title
        self.label = label
        self.options = options
        self.epher_args = epher_args or {}

        for item in self.children:
            item.label = self.title

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Enter Strike Amount", style=discord.ButtonStyle.secondary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

        self.modal = CustomModal(self.label, self.options, self.epher_args)

        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stop()


class GoogleSpreadsheetModification(discord.ui.View):
    def __init__(self, bot, config: dict, scopes: list, label: str, url: str):
        super().__init__(timeout=600.0)
        self.add_item(discord.ui.Button(label=label, url=url))
        self.bot = bot
        self.config = config
        self.scopes = scopes
        self.url = url

    @discord.ui.button(label="Request Ownership", style=discord.ButtonStyle.secondary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomModal(
            "Request Ownership",
            [
                (
                    "email",
                    discord.ui.TextInput(
                        placeholder="Email",
                        min_length=1,
                        max_length=100,
                        label="Email",
                        custom_id="email",
                    ),
                )
            ],
        )

        await interaction.response.send_modal(modal)

        timeout = await modal.wait()
        if timeout:
            return

        email = modal.email.value

        client = gspread.service_account_from_dict(self.config)
        sheet = client.open_by_url(self.url)
        client.insert_permission(sheet.id, value=email, perm_type="user", role="writer")
        permission_id = (sheet.list_permissions())[0]["id"]
        sheet.transfer_ownership(permission_id)

        self.remove_item(button)

        await interaction.edit_original_response(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Ownership Transferred",
                description="An ownership transfer request has been sent to your email.",
                color=GREEN_COLOR,
            ),
            view=self,
        )





class LinkView(discord.ui.View):
    def __init__(self, label: str, url: str):
        super().__init__(timeout=600.0)
        self.add_item(discord.ui.Button(label=label, url=url))


class RequestGoogleSpreadsheet(discord.ui.View):
    def __init__(
        self,
        bot,
        user_id,
        config: dict,
        scopes: list,
        data: list,
        template: str,
        total_seconds: int,
        type="lb",
        additional_data=None,
        label="Google Spreadsheet",
    ):
        self.bot = bot
        if type:
            self.type = type
        else:
            self.type = "lb"
        if additional_data:
            self.additional_data = additional_data
        else:
            self.additional_data = []

        super().__init__(timeout=600.0)
        self.user_id = user_id
        self.config = config
        self.scopes = scopes
        self.data = data
        self.template = template
        self.total_seconds = total_seconds
        if label:
            for item in self.children:
                item.label = label

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Google Spreadsheet", style=discord.ButtonStyle.secondary)
    async def googlespreadsheet(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if interaction.user.id != self.user_id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                )
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title="Generating...",
                description="We are currently generating your Google Spreadsheet.",
                color=BLANK_COLOR,
            )
        )

        client = gspread.service_account_from_dict(self.config)

        sheet: gspread.Spreadsheet = client.copy(
            self.template, interaction.guild.name, copy_permissions=True
        )
        new_sheet = sheet.get_worksheet(0)
        try:
            new_sheet.update_cell(4, 2, f'=IMAGE("{interaction.guild.icon.url}")')
        except AttributeError:
            pass

        if self.type == "lb":
            cell_list = new_sheet.range("D13:H999")
        elif self.type == "ar":
            cell_list = new_sheet.range("D13:I999")

        try:
            new_sheet.update_cell(
                12, 1, td_format(datetime.timedelta(seconds=self.total_seconds))
            )
        except OverflowError:
            pass

        for c, n_v in zip(cell_list, self.data):
            c.value = str(n_v)

        new_sheet.update_cells(cell_list, "USER_ENTERED")
        if self.type == "ar":
            LoAs = sheet.get_worksheet(1)
            LoAs.update_cell(4, 2, f'=IMAGE("{interaction.guild.icon.url}")')
            cell_list = LoAs.range("D13:H999")

            for cell, new_value in zip(cell_list, self.additional_data):
                if isinstance(new_value, int):
                    cell.value = f"=({new_value}/ 86400 + DATE(1970, 1, 1))"
                else:
                    cell.value = str(new_value)
            LoAs.update_cells(cell_list, "USER_ENTERED")

        client.insert_permission(
            sheet.id, value=None, perm_type="anyone", role="writer"
        )

        view = GoogleSpreadsheetModification(
            self.bot, self.config, self.scopes, "Open Google Spreadsheet", sheet.url
        )

        await interaction.edit_original_response(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Successfully generated",
                description="Your Google Spreadsheet has been successfully generated.",
                color=GREEN_COLOR,
            ),
            view=view,
        )

        self.stop()


#
# class LiveMenu(discord.ui.View):
#     def __init__(self, bot, ctx):
#         super().__init__(timeout=600.0)
#         self.bot = bot
#         self.context = ctx
#
#     async def execute_command(
#         self,
#         interaction: discord.Interaction,
#         arguments: str,
#         command: discord.ext.commands.HybridCommand = None,
#         extra_args: dict = None,
#         concatenate_to_last_argument: bool = False,
#         flag_class: discord.ext.commands.FlagConverter = DutyManageOptions,
#     ):
#         if command is None:
#             # assume default
#             command = self.bot.get_command("duty manage")
#         mockinteraction = copy(interaction)
#         mockinteraction._cs_command = command
#         mockinteraction.user = self.context.author
#
#         fakecontext = await discord.ext.commands.Context.from_interaction(
#             mockinteraction
#         )
#         mockcontext = copy(fakecontext)
#         can_run = await command.can_run(mockcontext)
#
#         if not can_run:
#             await interaction.response.send_message(
#                 content="<:ERMClose:1111101633389146223> You do not have permission to run this command!",
#                 ephemeral=True,
#             )
#             return
#
#         mockcontext.command = command
#         mockcontext.author = self.context.author
#
#         if not concatenate_to_last_argument:
#             await mockcontext.invoke(
#                 command,
#                 flags=await flag_class.convert(mockcontext, arguments),
#                 **extra_args,
#             )
#         else:
#             index = 0
#             for key, value in extra_args.copy().items():
#                 if index == len(extra_args) - 1:
#                     value += (" " + arguments)
#                     extra_args[key] = value
#                 index += 1
#
#
#             await mockcontext.invoke(
#                 command,
#                 **extra_args
#             )
#
#     @discord.ui.button(
#         label="On Duty", style=discord.ButtonStyle.green, custom_id="on_duty-execution"
#     )
#     async def on_duty(
#         self, interaction: discord.Interaction, button: discord.ui.Button
#     ):
#         await self.execute_command(
#             interaction, "/onduty=True /without_command_execution=True"
#         )
#
#     @discord.ui.button(
#         label="Toggle Break",
#         style=discord.ButtonStyle.secondary,
#         custom_id="toggle_break-execution",
#     )
#     async def toggle_break(
#         self, interaction: discord.Interaction, button: discord.ui.Button
#     ):
#         await self.execute_command(
#             interaction, "/togglebreak=True /without_command_execution=True"
#         )
#
#     @discord.ui.button(
#         label="Off Duty",
#         style=discord.ButtonStyle.danger,
#         custom_id="off_duty-execution",
#     )
#     async def off_duty(
#         self, interaction: discord.Interaction, button: discord.ui.Button
#     ):
#         await self.execute_command(
#             interaction, "/offduty=True /without_command_execution=True"
#         )
#
#     @discord.ui.button(
#         label="Log Punishment",
#         style=discord.ButtonStyle.secondary,
#         custom_id="punish-execution",
#         row=1,
#     )
#     async def _punish(self, interaction: discord.Interaction, button: discord.ui.Button):
#         self.user = None
#         self.punish_type = None
#         self.reason = None
#
#         class PunishModal(discord.ui.Modal):
#             def __init__(modal):
#                 super().__init__(title="Log Punishment", timeout=600.0)
#                 modal.add_item(
#                     discord.ui.TextInput(label="ROBLOX User", placeholder="ROBLOX User")
#                 )
#                 modal.add_item(
#                     discord.ui.TextInput(
#                         label="Punishment Type", placeholder="Punishment Type"
#                     )
#                 )
#                 modal.add_item(
#                     discord.ui.TextInput(label="Reason", placeholder="Reason")
#                 )
#
#             async def on_submit(modal, modal_interaction: discord.Interaction):
#                 for item in modal.children:
#                     if item.label == "ROBLOX User":
#                         self.user = item.value
#                     elif item.label == "Punishment Type":
#                         self.punish_type = item.value
#                     elif item.label == "Reason":
#                         self.reason = item.value
#                 await self.execute_command(
#                     modal_interaction,
#                     "\n/ephemeral=True /without_command_execution=True",
#                     command=self.bot.get_command("punish"),
#                     extra_args={
#                         "user": self.user,
#                         "type": self.punish_type,
#                         "reason": self.reason,
#                     },
#                     concatenate_to_last_argument=True,
#                     flag_class=PunishOptions,
#                 )
#
#         await interaction.response.send_modal(PunishModal())
#         self.user = None
#         self.punish_type = None
#         self.reason = None
#
#     @discord.ui.button(
#         label="Search",
#         style=discord.ButtonStyle.secondary,
#         custom_id="search-execution",
#         row=1,
#     )
#     async def _search(self, interaction: discord.Interaction, button: discord.ui.Button):
#         self.user = None
#
#         class SearchModal(discord.ui.Modal):
#             def __init__(modal):
#                 super().__init__(title="Search User", timeout=600.0)
#                 modal.add_item(
#                     discord.ui.TextInput(label="ROBLOX User", placeholder="ROBLOX User")
#                 )
#
#             async def on_submit(modal, modal_interaction: discord.Interaction):
#                 for item in modal.children:
#                     if item.label == "ROBLOX User":
#                         self.user = item.value
#                 await self.execute_command(
#                     modal_interaction,
#                     "/ephemeral=True /without_command_execution=True",
#                     command=self.bot.get_command("search"),
#                     extra_args={
#                         "query": self.user
#                     },
#                     flag_class=SearchOptions,
#                 )
#
#         await interaction.response.send_modal(SearchModal())
#         self.user = None
#
#     @discord.ui.button(
#         label="Active BOLOs",
#         style=discord.ButtonStyle.secondary,
#         custom_id="bolos-execution",
#         row=1,
#     )
#     async def _bolos(self, interaction: discord.Interaction, button: discord.ui.Button):
#         self.user = None
#
#         class SearchModal(discord.ui.Modal):
#             def __init__(modal):
#                 super().__init__(title="BOLO Search", timeout=600.0)
#                 modal.add_item(
#                     discord.ui.TextInput(label="ROBLOX User", placeholder="Optional, leave empty for all", required=False)
#                 )
#
#             async def on_submit(modal, modal_interaction: discord.Interaction):
#                 for item in modal.children:
#                     if item.label == "ROBLOX User":
#                         self.user = item.value
#                 args = {}
#                 if self.user.strip() != "":
#                     args['user'] = self.user
#
#                 await self.execute_command(
#                     modal_interaction,
#                     "/ephemeral=True /without_command_execution=True",
#                     command=self.bot.get_command("bolo active"),
#                     extra_args=args,
#                     flag_class=SearchOptions,
#                 )
#
#         await interaction.response.send_modal(SearchModal())
#         self.user = None





class MultiPaginatorMenu(discord.ui.View):
    def __init__(self, user_id, options: list, pages: dict):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

        self.add_item(MultiPaginatorDropdown(self.user_id, options, pages))


class WarningDropdownMenu(discord.ui.View):
    def __init__(self, user_id, options: list):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        new_options = []

        for option in options:
            if isinstance(option, discord.SelectOption):
                new_options.append(option)
            else:
                if isinstance(option, dict):
                    new_options.append(
                        discord.SelectOption(label=option["name"], value=option["name"])
                    )
                else:
                    new_options.append(discord.SelectOption(label=option, value=option))

        self.add_item(ChangeWarningType(self.user_id, new_options))


class ActivityNoticeAdministration(discord.ui.View):
    def __init__(
        self,
        bot,
        user_id: int,
        victim: int,
        guild_id: int,
        request_type: str,
        current_notice=None,
    ):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.value = None
        self.stored_interaction = None
        self.victim = victim
        self.bot = bot
        self.guild_id = guild_id
        self.request_type = request_type
        self.current_notice = current_notice

        if self.current_notice is not None:
            self.delete_button = discord.ui.Button(
                label="Delete", style=discord.ButtonStyle.danger
            )
            self.delete_button.callback = self.delete_notice
            self.add_item(self.delete_button)

            self.end_button = discord.ui.Button(
                label="End", style=discord.ButtonStyle.secondary
            )
            self.end_button.callback = self.end_notice
            self.add_item(self.end_button)

            self.extend_button = discord.ui.Button(
                label="Extend", style=discord.ButtonStyle.primary
            )
            self.extend_button.callback = self.extend_notice
            self.add_item(self.extend_button)

    async def visual_close(self, message: discord.Message):
        for item in self.children:
            self.remove_item(item)

        await message.edit(view=self)
        await message.delete()

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def create_notice(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.modal = CustomModal(
            "Create Activity Notice",
            [
                ("reason", discord.ui.TextInput(label="Reason")),
                ("duration", discord.ui.TextInput(label="Duration")),
            ],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stored_interaction = self.modal.interaction
        self.value = "create"

        await self.visual_close(interaction.message)
        self.stop()

    @discord.ui.button(label="List", style=discord.ButtonStyle.secondary)
    async def list_notices(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(thinking=False, ephemeral=True)
        self.stored_interaction = interaction
        self.value = "list"

        await self.visual_close(interaction.message)
        self.stop()

    async def delete_notice(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stored_interaction = interaction
        self.value = "delete"
        await self.visual_close(interaction.message)
        self.stop()

    async def end_notice(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stored_interaction = interaction
        self.value = "end"

        await self.visual_close(interaction.message)
        self.stop()

    async def extend_notice(self, interaction: discord.Interaction):
        self.modal = CustomModal(
            "Extend Activity Notice",
            [("duration", discord.ui.TextInput(label="Duration"))],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stored_interaction = self.modal.interaction
        self.value = "extend"
        await self.visual_close(interaction.message)
        self.stop()


class MultiSelectMenu(discord.ui.View):
    def __init__(self, user_id, options: list):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

        self.add_item(MultiDropdown(self.user_id, options))


class NextView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=600.0)

        button = self.children[0]
        button.emoji = discord.PartialEmoji.from_str(
            bot.emoji_controller.get_emoji("arrow")
        )

        self.user_id = user_id
        self.value = None

    @discord.ui.button(emoji="<:arrow:1169695690784518154>")
    async def _next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                )
            )
        self.value = True
        await interaction.response.defer()
        self.stop()




class PermissionTypeManagement(discord.ui.View):
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
                    color=blank_color,
                )
            )
        # await interaction.response.defer(thinking=False)
        self.modal = CustomModal(
            "Create Permission Type",
            [
                (
                    "permission_type_name",
                    discord.ui.TextInput(
                        label="Name", placeholder="Name of Permission Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.permission_type_name.value:
            self.name_for_creation = self.modal.permission_type_name.value
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
                    color=blank_color,
                )
            )
        # await interaction.response.defer(thinking=False)
        self.modal = CustomModal(
            "Edit Permission Type",
            [
                (
                    "permission_type_name",
                    discord.ui.TextInput(
                        label="Name", placeholder="Name of Permission Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.permission_type_name.value:
            self.name_for_creation = self.modal.permission_type_name.value
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
                    color=blank_color,
                )
            )
        self.modal = CustomModal(
            "Permission Type Deletion",
            [
                (
                    "permission_type",
                    discord.ui.TextInput(
                        label="Permission Type Name",
                        placeholder="Name of the Permission Type",
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.permission_type.value:
            self.selected_for_deletion = self.modal.permission_type.value
        else:
            return
        self.value = "delete"
        self.stop()



class AcknowledgeStaffRequest(discord.ui.View):
    def __init__(self, bot: commands.Bot, o_id: ObjectId):
        super().__init__(timeout=None)
        self.bot = bot
        self.o_id = o_id

    @discord.ui.button(label="Acknowledge", style=discord.ButtonStyle.secondary)
    async def acknowledge(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        document = await self.bot.staff_requests.db.find_one({"_id": self.o_id})
        if interaction.user.id in document["acked"]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Already Acknowledged",
                    description="You have already acknowledged this Staff Request.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
        document["acked"].append(interaction.user.id)
        await self.bot.staff_requests.db.update_one(
            {"_id": document["_id"]}, {"$set": {"acked": document["acked"]}}
        )
        embed = interaction.message.embeds[0]
        if embed.fields[-1].name.startswith("Acknowledgements"):
            index = len(embed.fields) - 1
            embed.set_field_at(
                index,
                name="Acknowledgements [{}]".format(len(document["acked"])),
                value="\n".join(["> <@{}>".format(u) for u in document["acked"]]),
            )
        else:
            embed.add_field(
                name="Acknowledgements [1]",
                value="\n".join(["> <@{}>".format(u) for u in document["acked"]]),
                inline=False,
            )

        await interaction.response.defer(thinking=False)
        await interaction.message.edit(embed=embed, view=self)


class BackNextView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=600.0)

        emojis = ["l_arrow", "arrow"]
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                array_idx = int(button.label) - 1
                button.emoji = discord.PartialEmoji.from_str(
                    bot.emoji_controller.get_emoji(emojis[array_idx])
                )
                button.label = ""

        self.user_id = user_id
        self.value = None

    @discord.ui.button(label="1", emoji="<:l_arrow:1169754353326903407>")
    async def _back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                )
            )
        self.value = -1
        self.stop()

    @discord.ui.button(label="2", emoji="<:arrow:1169695690784518154>")
    async def _next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                )
            )
        self.value = 1
        self.stop()



class ERLCIntegrationToolkit(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=900)
        self.selected_option = None
        self.user_id = user_id
        self.content = None
        self.message = None

    @discord.ui.button(label="Message", style=discord.ButtonStyle.secondary)
    async def message(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            modal := CustomModal(
                "Edit Message Content",
                [
                    (
                        "msg_content",
                        discord.ui.TextInput(
                            label="Message Content", max_length=250, required=True
                        ),
                    )
                ],
                {"ephemeral": True},
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        self.content = modal.msg_content.value
        self.selected_option = "Message"
        await self.message.edit(
            embed=discord.Embed(
                title="<:success:1163149118366040106> Success!",
                description="Message integration has successfully been setup.",
                color=GREEN_COLOR,
            ),
            view=None,
        )
        self.stop()

    @discord.ui.button(label="Hint", style=discord.ButtonStyle.secondary)
    async def hint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            modal := CustomModal(
                "Edit Hint Content",
                [
                    (
                        "hint_content",
                        discord.ui.TextInput(
                            label="Hint Content", max_length=250, required=True
                        ),
                    )
                ],
                {"thinking": False},
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        self.content = modal.hint_content.value
        self.selected_option = "Hint"

        await self.message.edit(
            embed=discord.Embed(
                title="<:success:1163149118366040106> Success!",
                description="Hint integration has successfully been setup.",
                color=GREEN_COLOR,
            ),
            view=None,
        )
        self.stop()


class ReminderCreationToolkit(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        dataset: dict,
        option: typing.Literal["create", "edit"],
        preset_values: dict | None = None,
    ):
        super().__init__(timeout=900.0)
        self.user_id = user_id
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
                if isinstance(item, discord.ui.Button):
                    if item.label == key:
                        item.label = value["label"]
                        item.style = value["style"]

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    async def refresh_ui(self, message: discord.Message):
        embed = discord.Embed(
            title=f"{self.option.title()} a Reminder",
            description=(
                f"> **Name:** {self.dataset['name']}\n"
                f"> **ID:** {self.dataset['id']}\n"
                f"> **Channel:** {'<#{}>'.format(self.dataset.get('channel', None)) if self.dataset.get('channel', None) is not None else 'Not set'}\n"
                f"> **Completion Ability:** {self.dataset.get('completion_ability') or 'Not set'}\n"
                f"> **Mentioned Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('role', [])]) or 'Not set'}\n"
                f"> **Interval:** {td_format(datetime.timedelta(seconds=self.dataset.get('interval', 0))) or 'Not set'}"
                f"\n\n**Content:**\n{self.dataset['message']}"
            ),
            color=BLANK_COLOR,
        )

        if all(
            [
                self.dataset.get("channel") is not None,
                self.dataset.get("interval") is not None,
            ]
        ):
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
        cls=discord.ui.RoleSelect, placeholder="Mentioned Roles", row=0, max_values=25
    )
    async def mentioned_roles_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        await interaction.response.defer()

        self.dataset["role"] = [i.id for i in select.values]
        await self.refresh_ui(interaction.message)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Reminder Channel",
        row=1,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        await interaction.response.defer()

        self.dataset["channel"] = [i.id for i in select.values][0]
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Set Interval", style=discord.ButtonStyle.secondary, row=2)
    async def set_interval(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.modal = CustomModal(
            "Set Interval",
            [
                (
                    "interval",
                    discord.ui.TextInput(
                        label="Interval",
                        placeholder="The interval between each reminder. (hours/minutes/seconds/days)",
                        default=str(self.dataset.get("interval", 0)),
                        required=False,
                    ),
                )
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        try:
            new_time = time_converter(self.modal.interval.value)
        except ValueError:
            return await self.modal.interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Time",
                    description="You did not enter a valid time.",
                    color=BLANK_COLOR,
                )
            )

        self.dataset["interval"] = new_time
        await self.refresh_ui(interaction.message)

    @discord.ui.button(
        label="Edit ER:LC Integration", style=discord.ButtonStyle.secondary, row=2
    )
    async def edit_integration(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        msg = await interaction.response.send_message(
            embed=discord.Embed(
                title="Edit ER:LC Integration",
                description="Here you can edit your reminder's integrations with Emergency Response: Liberty County, such as sending an automatic message or hint on a reminder activation. **As of right now, you can only have one integration type per reminder.**",
                color=BLANK_COLOR,
            ),
            ephemeral=True,
            view=(view := ERLCIntegrationToolkit(interaction.user.id)),
        )
        view.message = await interaction.original_response()
        timeout = await view.wait()
        if timeout:
            return
        selected_integration = view.selected_option
        content = view.content

        self.dataset["integration"] = {
            "type": selected_integration,
            "content": view.content,
        }
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Edit Content", style=discord.ButtonStyle.secondary, row=2)
    async def edit_content(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.modal = CustomModal(
            "Edit Content",
            [
                (
                    "content",
                    discord.ui.TextInput(
                        label="Content",
                        placeholder="The content of the reminder",
                        default=str(self.dataset.get("message", "")),
                        style=discord.TextStyle.long,
                        max_length=2000,
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        content = self.modal.content.value

        self.dataset["message"] = content
        await self.refresh_ui(interaction.message)

    @discord.ui.button(
        label="Completion Ability: Disabled", style=discord.ButtonStyle.danger, row=2
    )
    async def edit_completion_ability(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        if button.label == "Completion Ability: Disabled":
            self.dataset["completion_ability"] = True
            button.label = "Completion Ability: Enabled"
            button.style = discord.ButtonStyle.green
        else:
            self.dataset["completion_ability"] = False
            button.label = "Completion Ability: Disabled"
            button.style = discord.ButtonStyle.danger

        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This reminder has not been created.",
                color=BLANK_COLOR,
            )
        )
        await interaction.message.delete()
        self.stop()

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, disabled=True, row=3
    )
    async def finish(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer()
        self.cancelled = False
        self.stop()



class RDMActions(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Mark as Justified", style=discord.ButtonStyle.success)
    async def mark_as_justified(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            (
                modal := CustomModal(
                    "Reason",
                    [
                        (
                            "reason",
                            discord.ui.TextInput(
                                label="Reason",
                                placeholder="e.g. Event, Purge, etc.",
                                style=discord.TextStyle.long,
                            ),
                        )
                    ],
                    {"thinking": False},
                )
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        await interaction.message.edit(
            embed=interaction.message.embeds[0].add_field(
                name="Justification",
                value=f"> {modal.reason.value}\n- {interaction.user.mention}",
            ),
            view=self.clear_items(),
        )

    @discord.ui.button(label="Jail Player", style=discord.ButtonStyle.secondary)
    async def jail_player(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join([i if i in "1234567890" else "" for i in user_id])
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":kick {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Jailed Abuser",
                    description="This command has been sent to the server. They should now be jailed in the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(
        label="Kick Player",
        style=discord.ButtonStyle.secondary,
    )
    async def kick_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join([i if i in "1234567890" else "" for i in user_id])
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":kick {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Kicked Player",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(
        label="Ban Player",
        style=discord.ButtonStyle.secondary,
    )
    async def ban_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join([i if i in "1234567890" else "" for i in user_id])
        await interaction.response.defer(ephemeral=True, thinking=False)
        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":ban {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Banned Player",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )


class GameSecurityActions(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    def enable_reflective_action(self):
        # enables the button that allows for unbanning all affected users
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.label == "Unban Affected Players":
                    item.disabled = False

    @discord.ui.button(label="Mark as Justified", style=discord.ButtonStyle.success)
    async def mark_as_justified(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            (
                modal := CustomModal(
                    "Reason",
                    [
                        (
                            "reason",
                            discord.ui.TextInput(
                                label="Reason",
                                placeholder="e.g. SSD, permitted by owners, etc.",
                                style=discord.TextStyle.long,
                            ),
                        )
                    ],
                    {"thinking": False},
                )
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        await interaction.message.edit(
            embed=interaction.message.embeds[0].add_field(
                name="Justification",
                value=f"> {modal.reason.value}\n- {interaction.user.mention}",
            ),
            view=self.clear_items(),
        )

    @discord.ui.button(
        label="Unadmin Staff Member", style=discord.ButtonStyle.secondary
    )
    async def unadmin_staff_member(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")

        user_id = "".join(filter(str.isdigit, user_id))
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":unadmin {user_id}"
        )
        cr_2 = await bot.prc_api.run_command(interaction.guild.id, f":unmod {user_id}")

        for item in self.children:
            item.disabled = False
        await interaction.message.edit(view=self)

        if command_response[0] == 200 and cr_2[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Revoked Permissions",
                    description="This command has been sent to the server. Their permissions should now be removed.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(
        label="Unban Affected Players",
        style=discord.ButtonStyle.secondary,
        row=0,
        disabled=False,
    )
    async def unban_affected_players(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[1]

        users_ids = []
        affected_players = [
            i.strip() for i in field1.value.split("]:**")[1].split("\n")[0].split(", ")
        ]
        print(affected_players)
        users = [
            await bot.roblox.get_user_by_username(item) for item in affected_players
        ]
        print(users)
        for item in users:
            if item is not None:
                users_ids.append(str(item.id))

        await interaction.response.defer(ephemeral=True, thinking=False)
        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":unban {','.join(users_ids)}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Unbanned Affected Players",
                    description=f"This command has been sent to the server.\n\n-# **Command Executed:** `:unban {','.join(users_ids)}`",
                    color=GREEN_COLOR,
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description=f"This command has not been executed successfully.\n\n-# **Attempted Command:** `:unban {','.join(users_ids)}`",
                    color=BLANK_COLOR,
                )
            )

    @discord.ui.button(
        label="Kick Abuser", style=discord.ButtonStyle.secondary, row=1, disabled=True
    )
    async def kick_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join(filter(str.isdigit, user_id))
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":kick {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Kicked Abuser",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                )
            )

    @discord.ui.button(
        label="Ban Abuser", style=discord.ButtonStyle.secondary, row=1, disabled=True
    )
    async def ban_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join(filter(str.isdigit, user_id))
        await interaction.response.defer(ephemeral=True, thinking=False)
        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":ban {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Banned Abuser",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                )
            )



class CheckMark(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(emoji="✅", style=discord.ButtonStyle.gray)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

        await interaction.response.defer()
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(emoji="❎", style=discord.ButtonStyle.gray)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

        await interaction.response.defer()
        self.value = False
        self.stop()


class CompleteReminder(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=1200.0)

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Mark as Complete", style=discord.ButtonStyle.gray)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        embed.set_footer(
            text="Completed by {0.name}".format(interaction.user),
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = datetime.datetime.now()
        embed.color = GREEN_COLOR
        embed.title = (
            f"{self.bot.emoji_controller.get_emoji('success')} Reminder Completed"
        )

        for item in self.children:
            item.disabled = True
            item.label = "Completed"
            item.style = discord.ButtonStyle.green

        await interaction.message.edit(
            embed=embed,
            view=self,
        )

        self.stop()


class ReloadView(discord.ui.View):
    def __init__(self, bot, user_id: int, custom_callback: typing.Callable, args: list):
        super().__init__(timeout=900)
        self.bot = bot
        self.user_id = user_id
        self.custom_callback = custom_callback
        self.callback_args = args
        self.message = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def _temp_disable(self, timer: int):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        await asyncio.sleep(timer)
        for item in self.children:
            item.disabled = False
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(
        label="Reload",
        emoji="<:lastupdated:1176999148084535326>",
        style=discord.ButtonStyle.secondary,
    )
    async def _reload(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await self.custom_callback(*self.callback_args)
        await self._temp_disable(30)


class CustomCommandOptionSelect(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.modal = None
        self.value = None

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green, row=0)
    async def create_custom_command(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        self.value = "create"
        self.modal = CustomModal(
            "Create a Custom Command",
            [("name", discord.ui.TextInput(label="Custom Command Name"))],
            {"thinking": False},
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.name.value is None:
            return

        self.stop()

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.secondary, row=0)
    async def edit_custom_command(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        self.value = "edit"
        self.modal = CustomModal(
            "Edit a Custom Command",
            [("id", discord.ui.TextInput(label="Custom Command ID"))],
            {"thinking": False},
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.id.value is None:
            return
        self.stop()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, row=0)
    async def delete_custom_command(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        self.value = "delete"
        self.modal = CustomModal(
            "Delete a custom command",
            [
                (
                    "name",
                    discord.ui.TextInput(
                        placeholder="Command Name", label="Command Name"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.name.value is None:
            return
        self.stop()


class ShiftMenu(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        starting_state: typing.Literal["on", "break", "off"],
        user_id: int,
        shift_type: str,
        starting_document: dict | None = None,
        starting_container: ShiftItem | None = None,
    ):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.state = starting_state
        self.bot = bot
        self.shift_type = shift_type
        self.shift = starting_document
        self.contained_document = starting_container
        self.message = None

        self.check_buttons(self.state)

    def check_buttons(self, option: typing.Literal["on", "break", "off"]):
        if option == "on":
            buttons = ["Toggle Break", "Off-Duty"]
        elif option == "break":
            buttons = ["On-Duty", "Off-Duty"]
        else:
            buttons = ["On-Duty"]

        for item in self.children:
            if item.label not in buttons:
                item.disabled = True
            else:
                item.disabled = False

    async def interaction_check(self, interaction: Interaction, /) -> bool:

        if interaction.user.id == self.user_id:
            # Refresh current data to ensure state has not changed
            current_shift = await self.bot.shift_management.get_current_shift(
                interaction.user, interaction.guild.id
            )
            self.shift = current_shift
            if self.shift:
                self.contained_document = await self.bot.shift_management.fetch_shift(
                    self.shift["_id"]
                )
            else:
                self.contained_document = None
            if self.contained_document:
                if self.contained_document.breaks:
                    if self.contained_document.breaks[-1].end_epoch == 0:
                        self.state = "break"
                    else:
                        self.state = "on"
                else:
                    self.state = "on"
            else:
                self.state = "off"
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    async def cycle_ui(
        self, option: typing.Literal["on", "break", "off"], message: discord.Message
    ):
        shift = self.shift
        contained_document = self.contained_document
        if not contained_document and not shift:
            return
        uis = {
            "on": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftStarted')} **Shift Started**",
                color=GREEN_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Current Shift",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                ),
                inline=False,
            ),
            "off": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                color=RED_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Shift Overview",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Ended:** <t:{int(contained_document.end_epoch or datetime.datetime.now(tz=pytz.UTC).timestamp())}:R>"
                ),
                inline=False,
            ),
        }
        if option == "break":
            current_break = None
            for break_item in contained_document.breaks:
                logging.info(
                    f"Checking break: {break_item}"
                )  # Debugging log to print each break
                if (
                    break_item.end_epoch == 0
                ):  # Assuming end_epoch is 0 if the break hasn't ended yet
                    current_break = break_item
                    break

            if current_break:
                break_start_time = (
                    f"> **Break Started:** <t:{int(current_break.start_epoch)}:R>\n"
                )
            else:
                break_start_time = "> **Break Started:** No ongoing break\n"

            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftBreak')} **On-Break**",
                    color=ORANGE_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Shift Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"{break_start_time}"
                        f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                )
            )
        else:
            selected_ui = uis[option]

        if not selected_ui:
            return
        self.check_buttons(option)
        await message.edit(embed=selected_ui, view=self)

    async def on_timeout(self) -> None:
        if not self.message:
            for item in self.children:
                item.disabled = True

            return await self.message.edit(view=self)

    @discord.ui.button(label="On-Duty", style=discord.ButtonStyle.green)
    async def on_duty_button(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer(thinking=False)
        if self.state == "break":
            self.shift["Breaks"][-1]["EndEpoch"] = datetime.datetime.now(
                tz=pytz.UTC
            ).timestamp()
            self.shift["_id"] = self.contained_document.id
            await self.bot.shift_management.shifts.update_by_id(self.shift)
            await asyncio.sleep(1)
            self.contained_document = await self.bot.shift_management.fetch_shift(
                self.contained_document.id
            )
            await self.cycle_ui("on", interaction.message)
            self.bot.dispatch("break_end", self.contained_document.id)
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        access = True
        for item in settings.get("shift_management", {}).get("shift_types", []):
            if isinstance(item, dict):
                if item["name"] == self.shift_type:
                    access_roles = item.get("access_roles") or []
                    if len(access_roles) > 0:
                        access = False
                        for role in access_roles:
                            if role in [i.id for i in interaction.user.roles]:
                                access = True
                                break
        if not access:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Access",
                    description="You are not permitted to go on-duty as this Shift Type.",
                    color=blank_color,
                ),
                ephemeral=True,
            )

        if self.state == "on" or self.state == "break":
            return await self.cycle_ui(self.state, interaction.message)

        object_id = await self.bot.shift_management.add_shift_by_user(
            interaction.user, self.shift_type, [], interaction.guild.id
        )
        self.contained_document: ShiftItem = (
            await self.bot.shift_management.fetch_shift(object_id)
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(object_id)
        await self.cycle_ui("on", interaction.message)
        self.bot.dispatch("shift_start", self.shift["_id"])
        return

    @discord.ui.button(label="Toggle Break", style=discord.ButtonStyle.secondary)
    async def toggle_break_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        self.shift["Breaks"].append(
            {
                "StartEpoch": datetime.datetime.now(tz=pytz.UTC).timestamp(),
                "EndEpoch": 0,
            }
        )
        self.shift["_id"] = self.contained_document.id
        await self.bot.shift_management.shifts.update_by_id(self.shift)
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        await self.cycle_ui("break", interaction.message)
        self.bot.dispatch("break_start", self.contained_document.id)
        return

    @discord.ui.button(label="Off-Duty", style=discord.ButtonStyle.red)
    async def off_duty_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        await self.bot.shift_management.end_shift(
            self.contained_document.id, self.contained_document.guild
        )
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(
            self.contained_document.id
        )
        await self.cycle_ui("off", interaction.message)
        try:
            self.bot.dispatch("shift_end", self.contained_document.id)
        except Exception as e:
            logging.info(f"Error dispatching shift_end: {e}")
        return


class AdministratedShiftMenu(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        starting_state: typing.Literal["on", "break", "off"],
        user_id: int,
        target_id: int,
        shift_type: str,
        starting_document: dict | None = None,
        starting_container: ShiftItem | None = None,
    ):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.target_id = target_id
        self.state = starting_state
        self.bot = bot
        self.shift_type = shift_type
        self.shift = starting_document
        self.contained_document = starting_container
        self.message = None

        self.check_buttons(self.state)

    def check_buttons(self, option: typing.Literal["on", "break", "off"]):
        if option == "on":
            buttons = ["Toggle Break", "Off-Duty", "Other Options"]
        elif option == "break":
            buttons = ["On-Duty", "Off-Duty", "Other Options"]
        else:
            buttons = ["On-Duty", "Other Options"]

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.label not in buttons:
                    item.disabled = True
                else:
                    item.disabled = False

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    async def cycle_ui(
        self,
        option: typing.Literal["on", "break", "off", "void"],
        message: discord.Message,
    ):
        shift = self.shift
        contained_document = self.contained_document
        previous_shifts = [
            i
            async for i in self.bot.shift_management.shifts.db.find(
                {
                    "UserID": self.target_id,
                    "Guild": message.guild.id,
                    "EndEpoch": {"$ne": 0},
                }
            )
        ]
        self.state = option
        if option == "void":
            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                    color=RED_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Statistics",
                    value=(
                        f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n"
                        f"> **Total Shifts:** {len(previous_shifts)}\n"
                        f"> **Average Shift Duration:** {td_format(datetime.timedelta(seconds=(sum([get_elapsed_time(item) for item in previous_shifts]).__truediv__(len(previous_shifts) or 1))))}\n"
                    ),
                    inline=False,
                )
            )
        elif option not in ["void", "break"]:
            if not contained_document:
                return
            uis = {
                "on": discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftStarted')} **Shift Started**",
                    color=GREEN_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Statistics",
                    value=(
                        f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n"
                        f"> **Total Shifts:** {len(previous_shifts)}\n"
                        f"> **Average Shift Duration:** {td_format(datetime.timedelta(seconds=(sum([get_elapsed_time(item) for item in previous_shifts]).__truediv__(len(previous_shifts) or 1))))}\n"
                    ),
                    inline=False,
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"> **Breaks:** {len(contained_document.breaks)}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                ),
                "off": discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                    color=RED_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Shift Overview",
                    value=(
                        f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"> **Breaks:** {len(contained_document.breaks)}\n"
                        f"> **Ended:** <t:{int(contained_document.end_epoch or datetime.datetime.now(tz=pytz.UTC).timestamp())}:R>"
                    ),
                    inline=False,
                ),
            }
        if option == "break":
            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftBreak')} **On-Break**",
                    color=ORANGE_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Statistics",
                    value=(
                        f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n"
                        f"> **Total Shifts:** {len(previous_shifts)}\n"
                        f"> **Average Shift Duration:** {td_format(datetime.timedelta(seconds=(sum([get_elapsed_time(item) for item in previous_shifts]).__truediv__(len(previous_shifts) or 1))))}\n"
                    ),
                    inline=False,
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Shift Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"> **Break Started:** <t:{int(contained_document.breaks[0].start_epoch)}:R>\n"
                        f"> **Breaks:** {len(contained_document.breaks)}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                )
            )
        elif option not in ["void", "break"]:
            selected_ui = uis[option]

        # if not selected_ui:
        #     return
        self.check_buttons(option)
        await message.edit(embed=selected_ui, view=self)

    async def on_timeout(self) -> None:
        if not self.message:
            for item in self.children:
                item.disabled = True

            return await self.message.edit(view=self)

    async def _manipulate_shift_time(
        self, message, op: typing.Literal["add", "subtract"], amount: int
    ):
        self.message = message
        member = await self.message.guild.fetch_member(self.target_id)
        guild = self.message.guild

        operations = {
            "add": self.bot.shift_management.add_time_to_shift,
            "subtract": self.bot.shift_management.remove_time_from_shift,
        }

        chosen_operation = operations[op]
        if self.contained_document is not None:
            check_for_update = await self.bot.shift_management.shifts.find_by_id(
                ObjectId(self.shift["_id"])
            )
            if check_for_update != self.shift:
                self.shift = check_for_update
                self.contained_document = await self.bot.shift_management.fetch_shift(
                    self.shift["_id"]
                )

        if self.contained_document is not None:
            if self.contained_document.end_epoch == 0:
                await chosen_operation(self.contained_document.id, amount)
                new_contained_document = await self.bot.shift_management.fetch_shift(
                    self.contained_document.id
                )
                self.contained_document = new_contained_document
                self.shift = await self.bot.shift_management.shifts.find_by_id(
                    self.contained_document.id
                )

                self.bot.dispatch(
                    "shift_edit",
                    self.contained_document.id,
                    "added_time" if op == "add" else "removed_time",
                    (await self.message.guild.fetch_member(self.user_id)),
                )
                return

        oid = await self.bot.shift_management.add_shift_by_user(
            member, self.shift_type, [], guild.id
        )
        await chosen_operation(oid, amount)
        await self.bot.shift_management.end_shift(oid, guild.id)
        self.contained_document = None
        self.shift = None

    @discord.ui.button(label="On-Duty", style=discord.ButtonStyle.green)
    async def on_duty_button(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer(thinking=False)
        if self.state == "break":
            self.shift["Breaks"][-1]["EndEpoch"] = datetime.datetime.now(
                tz=pytz.UTC
            ).timestamp()
            self.shift["_id"] = self.contained_document.id
            await self.bot.shift_management.shifts.update_by_id(self.shift)
            self.contained_document = await self.bot.shift_management.fetch_shift(
                self.contained_document.id
            )
            await self.cycle_ui("on", interaction.message)
            self.bot.dispatch("break_end", self.contained_document.id)
            return

        object_id = await self.bot.shift_management.add_shift_by_user(
            await interaction.guild.fetch_member(self.target_id),
            self.shift_type,
            [],
            interaction.guild.id,
        )
        self.contained_document: ShiftItem = (
            await self.bot.shift_management.fetch_shift(object_id)
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(object_id)
        await self.cycle_ui("on", interaction.message)
        self.bot.dispatch("shift_start", self.shift["_id"])
        return

    @discord.ui.button(label="Toggle Break", style=discord.ButtonStyle.secondary)
    async def toggle_break_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        self.shift["Breaks"].append(
            {
                "StartEpoch": datetime.datetime.now(tz=pytz.UTC).timestamp(),
                "EndEpoch": 0,
            }
        )
        self.shift["_id"] = self.contained_document.id
        await self.bot.shift_management.shifts.update_by_id(self.shift)
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        await self.cycle_ui("break", interaction.message)
        self.bot.dispatch("break_start", self.contained_document.id)
        return

    @discord.ui.button(label="Off-Duty", style=discord.ButtonStyle.red)
    async def off_duty_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        await self.bot.shift_management.end_shift(
            self.contained_document.id, self.contained_document.guild
        )
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(
            self.contained_document.id
        )
        await self.cycle_ui("off", interaction.message)
        self.bot.dispatch("shift_end", self.contained_document.id)
        return

    @discord.ui.select(
        placeholder="Other Options",
        options=[
            discord.SelectOption(
                label="Add Time",
                value="add",
                description="Add time to an ongoing shift.",
            ),
            discord.SelectOption(
                label="Subtract Time",
                value="subtract",
                description="Subtract time to an ongoing shift.",
            ),
            discord.SelectOption(
                label="Void shift",
                value="void",
                description="Void an ongoing shift.",
            ),
            discord.SelectOption(
                label="Clear Member Shifts",
                value="clear",
                description="Remove all shifts associated with this member.",
            ),
        ],
        row=1,
    )
    async def other_options(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = select.values[0]
        if value not in ["add", "subtract"]:
            await interaction.response.defer(thinking=False)
        if value == "add":
            self.modal = CustomModal(
                title="Add Time",
                options=[
                    (
                        "time",
                        discord.ui.TextInput(
                            label="Time",
                            placeholder="How much time to add to this shift?",
                        ),
                    )
                ],
                epher_args={"ephemeral": True, "thinking": False},
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            unfiltered = self.modal.time.value
            try:
                converted = time_converter(unfiltered)
            except ValueError:
                return await self.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Time",
                        description="I could not convert this time. Please try again.",
                        color=BLANK_COLOR,
                    )
                )
            except OverflowError:
                return await self.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Time",
                        description="You can't add more than 6 months in shift time.",
                        color=BLANK_COLOR,
                    )
                )

            await self._manipulate_shift_time(interaction.message, "add", converted)
            settings = await self.bot.settings.find_by_id(interaction.guild.id)
            previous_shifts = [
                i
                async for i in self.bot.shift_management.shifts.db.find(
                    {
                        "UserID": self.target_id,
                        "Guild": interaction.guild.id,
                        "EndEpoch": {"$ne": 0},
                    }
                )
            ]
            if settings.get("shift_management", {}).get("channel"):
                log_channel = interaction.guild.get_channel(
                    settings["shift_management"]["channel"]
                )
                if log_channel:
                    embed = discord.Embed(
                        title="Shift Time Added",
                        description=(
                            f"> **User:** <@{self.target_id}> \n"
                            f"> **Shift Type:** {self.shift_type}\n"
                            f"> **Time Added:** {td_format(datetime.timedelta(seconds=converted))}"
                        ),
                        color=0x2F3136,
                    )
                    embed.add_field(
                        name="Added By:", value=f"> {interaction.user.mention}"
                    )
                    embed.add_field(
                        name="New Total Shift Time:",
                        value=f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n",
                        inline=False,
                    )
                    embed.set_thumbnail(
                        url=interaction.guild.get_member(
                            self.target_id
                        ).display_avatar.url
                    )
                    await log_channel.send(embed=embed)
            await asyncio.sleep(0.02)
            # # print(t(t(t(t(self.state)
            if self.state not in ["void", "off"]:
                await self.cycle_ui(self.state, interaction.message)
            else:
                await self.cycle_ui("void", interaction.message)
        elif value == "subtract":
            self.modal = CustomModal(
                title="Subtract Time",
                options=[
                    (
                        "time",
                        discord.ui.TextInput(
                            label="Time",
                            placeholder="How much time to subtract from this shift?",
                        ),
                    )
                ],
                epher_args={"ephemeral": True, "thinking": False},
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            unfiltered = self.modal.time.value
            try:
                converted = time_converter(unfiltered)
            except ValueError:
                return await self.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Time",
                        description="I could not convert this time. Please try again.",
                        color=BLANK_COLOR,
                    )
                )

            await self._manipulate_shift_time(
                interaction.message, "subtract", converted
            )
            settings = await self.bot.settings.find_by_id(interaction.guild.id)
            previous_shifts = [
                i
                async for i in self.bot.shift_management.shifts.db.find(
                    {
                        "UserID": self.target_id,
                        "Guild": interaction.guild.id,
                        "EndEpoch": {"$ne": 0},
                    }
                )
            ]
            if settings.get("shift_management", {}).get("channel"):
                log_channel = interaction.guild.get_channel(
                    settings["shift_management"]["channel"]
                )
                if log_channel:
                    embed = discord.Embed(
                        title="Shift Time Subtracted",
                        description=(
                            f"> **User:** <@{self.target_id}> \n"
                            f"> **Shift Type:** {self.shift_type}\n"
                            f"> **Time Subtracted:** {td_format(datetime.timedelta(seconds=converted))}"
                        ),
                        color=0x2F3136,
                    )
                    embed.add_field(
                        name="Subtracted By:", value=f"> {interaction.user.mention}"
                    )
                    embed.add_field(
                        name="New Total Shift Time:",
                        value=f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n",
                        inline=False,
                    )
                    embed.set_thumbnail(
                        url=interaction.guild.get_member(
                            self.target_id
                        ).display_avatar.url
                    )
                    await log_channel.send(embed=embed)
            await asyncio.sleep(0.02)
            # # print(t(t(t(t(self.state)
            if self.state not in ["void", "off"]:
                await self.cycle_ui(self.state, interaction.message)
            else:
                await self.cycle_ui("void", interaction.message)

        elif value == "void":
            if not self.contained_document:
                try:
                    self.contained_document = (
                        await self.bot.shift_management.fetch_shift(self.shift["_id"])
                    )
                except TypeError:
                    return

            self.bot.dispatch(
                "shift_void", interaction.user, self.contained_document.id
            )
            await asyncio.sleep(2)
            await self.bot.shift_management.shifts.delete_by_id(
                self.contained_document.id
            )
            self.contained_document = None
            self.shift = None
            await self.cycle_ui("void", interaction.message)

        elif value == "clear":
            all_target_shifts = [
                shift
                async for shift in self.bot.shift_management.shifts.db.find(
                    {"UserID": self.target_id, "Guild": interaction.guild.id}
                )
            ]
            for item in all_target_shifts:
                await self.bot.shift_management.shifts.delete_by_id(item["_id"])
            self.shift = None
            self.contained_document = None
            await self.cycle_ui("void", interaction.message)



class ManagementOptions(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.value = None

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(label="Manage Types")
    async def manage_types(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return
        await interaction.response.defer(thinking=False)
        self.value = "types"
        self.stop()

    @discord.ui.button(label="Modify Punishment")
    async def modify_punishment(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return
        self.modal = CustomModal(
            "Modify Punishment",
            [("punishment_id", discord.ui.TextInput(label="Punishment ID"))],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if not self.modal.punishment_id.value:
            return

        self.value = "modify"
        self.stop()


class ManageTypesView(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.value = None
        self.user_id = user_id
        self.selected_for_deletion = None
        self.name_for_creation = None

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def create_punishment_type(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return
        modal = CustomModal(
            "Create Type",
            [
                (
                    "punishment_type",
                    discord.ui.TextInput(
                        label="Punishment Type Name",
                        placeholder="Name of the punishment type you want to create.",
                    ),
                )
            ],
        )
        await interaction.response.send_modal(modal)
        await modal.wait()
        if not modal.punishment_type.value:
            return
        self.name_for_creation = modal.punishment_type.value
        self.value = "create"
        self.stop()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_punishment_type(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        val = await self.interaction_check(interaction)
        if not val:
            return

        modal = CustomModal(
            "Delete Type",
            [
                (
                    "punishment_type",
                    discord.ui.TextInput(
                        label="Punishment Type ID",
                        placeholder="ID of the punishment type you want to delete.",
                    ),
                )
            ],
        )
        await interaction.response.send_modal(modal)
        await modal.wait()
        if not modal.punishment_type.value:
            return
        self.selected_for_deletion = modal.punishment_type.value
        self.value = "delete"
        self.stop()


class PunishmentTypeCreator(discord.ui.View):
    def __init__(self, user_id: int, dataset: dict):
        super().__init__(timeout=900.0)
        self.user_id = user_id
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
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    async def refresh_ui(self, message: discord.Message):
        embed = discord.Embed(
            title="Punishment Type Creation",
            description=(
                f"> **Name:** {self.dataset['name']}\n"
                f"> **ID:** {self.dataset['id']}\n"
                f"> **Punishment Channel:** {'<#{}>'.format(self.dataset.get('channel', None)) if self.dataset.get('channel', None) is not None else 'Not set'}\n"
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
        cls=discord.ui.ChannelSelect,
        placeholder="Punishment Channel",
        row=1,
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

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This Punishment Type has not been created.",
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


class PunishmentModifier(discord.ui.View):
    def __init__(self, bot, user_id: int, dataset: dict):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.restored_interaction = None
        self.bot = bot
        self.dataset = dataset
        self.root_dataset = dataset
        self.cancelled = None

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
            return False

    async def refresh_ui(self, message: discord.Message):
        embed = discord.Embed(
            title="Punishment Modification",
            description=(
                f"> **Username:** {self.dataset['Username']}\n"
                f"> **Type:** {self.dataset['Type']}\n"
                f"> **ID:** {self.dataset['Snowflake']}\n"
                f"> **Reason:** {self.dataset['Reason']}"
            ),
            color=BLANK_COLOR,
        )

        await message.edit(embed=embed, view=self)

    @discord.ui.button(label="Change Type", row=0)
    async def change_type(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = CustomModal(
            "Edit Punishment Type",
            [("punishment_type", discord.ui.TextInput(label="Punishment Type Name"))],
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        try:
            chosen_type = modal.punishment_type.value
        except ValueError:
            return

        punishment_types = (
            await self.bot.punishment_types.get_punishment_types(interaction.guild.id)
        ) or {"types": []}
        chosen_identifier = None
        for item in punishment_types["types"] + ["Warning", "Kick", "Ban", "BOLO"]:
            if isinstance(item, str) and item.lower() == chosen_type.lower():
                chosen_identifier = item
                break
            elif isinstance(item, dict) and item["name"].lower() == chosen_type.lower():
                chosen_identifier = item["name"]
                break

        if not chosen_identifier:
            return await modal.interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find type",
                    description="This punishment type does not exist.",
                    color=BLANK_COLOR,
                )
            )

        self.dataset["Type"] = chosen_identifier
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Edit Reason", row=0)
    async def edit_reason(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = CustomModal(
            "Edit Reason", [("reason", discord.ui.TextInput(label="Reason"))]
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        self.dataset["Reason"] = modal.reason.value
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Delete Punishment", row=0)
    async def delete_punishment(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):

        punishment = await self.bot.punishments.db.find_one(self.root_dataset)
        if punishment:
            await self.bot.punishments.remove_warning_by_snowflake(
                punishment["Snowflake"]
            )
            await interaction.message.delete()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Punishment Deleted",
                    color=GREEN_COLOR,
                    description="This punishment has been deleted successfully!",
                )
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This punishment has not been modified.",
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
        label="Finish", style=discord.ButtonStyle.green, disabled=False, row=3
    )
    async def finish(self, interaction: discord.Interaction, _: discord.Button):
        punishment = await self.bot.punishments.find_by_id(self.dataset["_id"])
        if punishment:
            await self.bot.punishments.upsert(self.dataset)
        self.cancelled = False
        self.stop()




class AvatarCheckView(discord.ui.View):
    def __init__(self, bot, user_id: str, message: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.message = message

    @discord.ui.button(label="Mark as Reviewed", style=discord.ButtonStyle.success)
    async def mark_reviewed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = interaction.message.embeds[0]
        embed.title = f"{self.bot.emoji_controller.get_emoji('success')} Unrealistic Avatar Reviewed"
        embed.color = GREEN_COLOR

        for item in self.children:
            item.disabled = True
            if item.label == "Mark as Reviewed":
                item.label = f"Reviewed by {interaction.user.name}"

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.defer()

    @discord.ui.button(label="Kick Player", style=discord.ButtonStyle.secondary)
    async def kick_player(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.bot.prc_api.run_command(
                interaction.guild.id, f":kick {self.user_id}"
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Kicked Player",
                    description="The player has been kicked from the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
            for item in self.children:
                if item == button:
                    item.disabled = True

            await interaction.message.edit(view=self)

        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed",
                    description=f"Failed to kick player: {str(e)}",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )


class APIKeyConfirmation(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=600.0)
        self.user_id = user_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.id == self.user_id:
            return True
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Not Permitted",
                description="You are not permitted to interact with these buttons.",
                color=blank_color,
            ),
            ephemeral=True,
        )
        return False

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(thinking=False)
        self.value = True
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        self.value = False
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        self.stop()


class RefreshConfirmation(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30.0)
        self.value = None
        self.author_id = author_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
        await interaction.response.defer()
        self.value = True
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=blank_color,
                ),
                ephemeral=True,
            )
        await interaction.response.defer()
        self.value = False
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass


