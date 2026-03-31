import discord, datetime
from utils.constants import BLANK_COLOR
from .custommodal import CustomModal
from utils.utils import time_converter
from utils.timestamp import td_format
from discord import Interaction
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
