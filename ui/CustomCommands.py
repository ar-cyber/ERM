import discord
from discord import Interaction
from utils.constants import BLANK_COLOR
from .MiscButtons import ButtonCustomisation
from ui.CustomModals import CustomModal
from .MessageCustomisation import MessageCustomisation
from utils.utils import generalised_interaction_check_failure

class RemoveCustomCommand(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    @discord.ui.button(
        label="Delete a custom command", style=discord.ButtonStyle.danger
    )
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

class CustomCommandSettings(discord.ui.Modal, title="Custom Command Settings"):
    name = discord.ui.TextInput(
        label="Custom Command Name",
        placeholder="e.g. ssu",
        style=discord.TextStyle.short,
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()
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
                    color=BLANK_COLOR,
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

class CustomCommandModification(discord.ui.View):
    def __init__(self, user_id: int, command_data: dict):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.value = None
        self.command_data = command_data

        if self.command_data.get("channel") is not None:
            for select in list(
                filter(lambda x: isinstance(x, discord.ui.ChannelSelect), self.children)
            ):
                select.default_values = [
                    discord.Object(id=self.command_data.get("channel"))
                ]

    async def check_ability(self, message):
        if self.command_data.get("message", None) and self.command_data.get(
            "name", None
        ):
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.label == "Finish":
                        item.disabled = False

            await message.edit(view=self)
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.label == "Finish":
                        item.disabled = True
            await message.edit(view=self)

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
            title="Custom Commands",
            description=(
                "**Command Information**\n"
                f"> **Command ID:** `{self.command_data['id']}`\n"
                f"> **Command Name:** {self.command_data['name']}\n"
                f"> **Creator:** <@{self.command_data['author']}>\n"
                f"> **Default Channel:** {'<#{}>'.format(self.command_data.get('channel')) if self.command_data.get('channel') is not None else 'None selected'}\n"
                f"\n**Message:**\n"
                f"View the message below by clicking 'View Message'."
            ),
            color=BLANK_COLOR,
        )
        await message.edit(embed=embed)

    @discord.ui.button(label="View Variables", row=0)
    async def view_variables(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        return await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    "With **ERM Custom Commands**, you can use custom variables to adapt to the current circumstances when the command is ran.\n"
                    "`{user}` - Mention of the person using the command.\n"
                    "`{username}` - Name of the person using the command.\n"
                    "`{display_name}` - Display name of the person using the command.\n"
                    "`{time}` - Timestamp format of the time of the command execution.\n"
                    "`{server}` - Name of the server this is being ran in.\n"
                    "`{channel}` - Mention of the channel the command is being ran in.\n"
                    "`{prefix}` - The custom prefix of the bot.\n"
                    "`{onduty}` - Number of staff which are on duty within your server.\n"
                    "\n**PRC Specific Variables**\n"
                    "`{join_code}` - Join Code of the ER:LC server\n"
                    "`{players}` - Current players in the ER:LC server\n"
                    "`{max_players}` - Maximum players of the ER:LC server\n"
                    "`{queue}` - Number of players in the queue\n"
                    "`{staff}` - Number of staff members in-game\n"
                    "`{mods}` - Number of mods in-game\n"
                    "`{admins}` - Number of admins in-game\n"
                ),
                color=BLANK_COLOR,
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="Edit Name", row=0)
    async def edit_custom_command_name(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = CustomModal(
            "Edit Custom Command Name",
            [
                (
                    "name",
                    discord.ui.TextInput(label="Custom Command Name", max_length=50),
                )
            ],
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        try:
            chosen_identifier = modal.name.value
        except ValueError:
            return

        if not chosen_identifier:
            return

        self.command_data["name"] = chosen_identifier
        await self.check_ability(interaction.message)
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="View Message", row=0)
    async def view_custom_command_message(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)

        async def _return_failure():
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="No Message Found",
                    description="There is currently no message associated with this Custom Command.\nYou can add one using 'Edit Message'.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        view = discord.ui.View()
        for item in self.command_data.get("buttons") or []:
            view.add_item(
                discord.ui.Button(
                    label=item["label"],
                    url=item["url"],
                    row=item["row"],
                    style=discord.ButtonStyle.url,
                )
            )

        if not self.command_data.get("message", None):
            return await _return_failure()

        if (
            not self.command_data.get("message", {}).get("content", None)
            and not len(self.command_data.get("message", {}).get("embeds", [])) > 0
        ):
            return await _return_failure()

        converted = []
        for item in self.command_data.get("message").get("embeds", []):
            converted.append(discord.Embed.from_dict(item))

        await interaction.followup.send(
            embeds=converted,
            content=self.command_data["message"].get("content", None),
            ephemeral=True,
            view=view,
        )

    @discord.ui.button(label="Edit Message", row=0)
    async def edit_message(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        view = MessageCustomisation(
            interaction.user.id,
            self.command_data.get("message", None),
            external=False,
            persist=False,
        )
        view.sustained_interaction = interaction

        if not self.command_data.get("message", None):
            await interaction.response.send_message(view=view, ephemeral=True)
        else:
            converted = []
            for item in self.command_data.get("message", {}).get("embeds", []):
                converted.append(discord.Embed.from_dict(item))

            await interaction.response.send_message(
                content=self.command_data.get("message", {}).get("content", None),
                embeds=converted,
                view=view,
                ephemeral=True,
            )

        await view.wait()
        if view.newView:
            await view.newView.wait()
            chosen_message = view.newView.msg
        else:
            chosen_message = view.msg

        new_content = chosen_message.content
        new_embeds = []
        for item in chosen_message.embeds or []:
            new_embeds.append(item.to_dict())

        self.command_data["message"] = {"content": new_content, "embeds": new_embeds}
        await self.check_ability(interaction.message)
        await self.refresh_ui(interaction.message)
        await (await interaction.original_response()).delete()

    @discord.ui.button(label="Edit Buttons", row=0)
    async def edit_buttons(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        view = ButtonCustomisation(self.command_data, interaction.user.id)
        view.sustained_interaction = interaction

        if not self.command_data.get("message", None):
            await interaction.response.send_message(view=view, ephemeral=True)
        else:
            converted = []
            for item in self.command_data.get("message", {}).get("embeds", []):
                converted.append(discord.Embed.from_dict(item))

            await interaction.response.send_message(
                content=self.command_data.get("message", {}).get("content", None),
                embeds=converted,
                view=view,
                ephemeral=True,
            )

        timeout = await view.wait()
        if timeout or not view.value:
            return

        self.command_data["buttons"] = view.command_data.get("buttons", [])
        await self.check_ability(interaction.message)
        await self.refresh_ui(interaction.message)
        await (await interaction.original_response()).delete()

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Default Channel",
        row=1,
        min_values=0,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = await self.interaction_check(interaction)
        if not value:
            return

        self.command_data["channel"] = (
            select.values[0].id if len(select.values) > 0 else None
        )
        await interaction.response.defer(thinking=False)
        await self.check_ability(interaction.message)
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=2)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        self.value = False
        pass

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, row=2, disabled=True
    )
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        self.value = True
        self.stop()
