import discord, typing
from utils.utils import generalised_interaction_check_failure
from utils.constants import BLANK_COLOR, GREEN_COLOR
from .CustomModals import CustomModal
from discord import Interaction
from discord.ext import commands
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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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

