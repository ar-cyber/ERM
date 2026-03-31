import discord, typing, datetime
from utils.utils import generalised_interaction_check_failure
from .CustomModals import CustomModal
from utils.constants import BLANK_COLOR, GREEN_COLOR

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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )


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

