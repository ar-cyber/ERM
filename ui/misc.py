import discord
from .CustomModals import CustomModal
from utils.utils import generalised_interaction_check_failure
from utils.constants import BLANK_COLOR, GREEN_COLOR
from discord.ext import commands
from bson import ObjectId
from discord import Interaction
# ACKNOWLEDGE MENU
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

# ENABLE/DISABLE MENU
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

# BackNextView???
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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
                )
            )
        self.value = 1
        self.stop()

# idk honestly

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

# av checks

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

# Staff requests
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
                color=BLANK_COLOR,
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

# permission types???

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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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


# MANAGEMENTOPTIONS

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
                    color=BLANK_COLOR,
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