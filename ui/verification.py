import discord, typing
from utils.utils import generalised_interaction_check_failure
import random
from utils.constants import BLANK_COLOR, GREEN_COLOR
from discord.ext import commands
from .custommodal import CustomModal

class RobloxUsername(discord.ui.Modal, title="Verification"):
    name = discord.ui.TextInput(
        label="Roblox Username",
        placeholder="e.g. Android365436",
        max_length=32,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stop()

class EnterRobloxUsername(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.modal: typing.Union[None, RobloxUsername] = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        self.modal = RobloxUsername()
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stop()


class Verification(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.modal: typing.Union[None, RobloxUsername] = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Done!", style=discord.ButtonStyle.green, emoji="✅")
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

        await interaction.response.defer()

        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

        self.value = "done"
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

        await interaction.response.defer()

        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

        self.value = "cancel"
        self.stop()


class CompleteVerification(discord.ui.View):
    def __init__(self, user: discord.Member):
        self.user = user
        super().__init__(timeout=600.0)

    @discord.ui.button(
        label="I have changed my description", style=discord.ButtonStyle.success
    )
    async def changed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to utilise these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        await interaction.response.defer(thinking=False, ephemeral=False)
        self.stop()



class AccountLinkingMenu(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        user: discord.Member,
        sustained_interaction: discord.Interaction,
    ):
        self.bot = bot
        self.user = user
        self.mode = "OAuth2"
        self.associated = None
        self.sustained_interaction = sustained_interaction

        super().__init__(timeout=600.0)
        self.add_item(
            discord.ui.Button(
                label="Link Roblox",
                url=f"https://authorize.roblox.com/?client_id=6127131307610842685&response_type=code&redirect_uri=https://verify.ermbot.xyz/auth&scope=openid+profile&state={self.user.id}",
            )
        )

    @discord.ui.button(label="Legacy Code Verification", row=1)
    async def code_verification(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Authorized",
                    description="You are not authorized to utilise this menu.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return

        msg = self.sustained_interaction.message if self.sustained_interaction else None
        modal = CustomModal(
                    "Legacy Code Verification",
                    [
                        (
                            "username",
                            (
                                discord.ui.TextInput(
                                    label="Roblox Username",
                                    placeholder="Roblox Username (e.g. i_iMikey)",
                                    required=True,
                                )
                            ),
                        )
            ],
        )
        await interaction.response.send_modal(
            modal
        )
        timeout = await modal.wait()
        if timeout:
            return
        if not modal.username.value:
            return

        try:
            user = await self.bot.roblox.get_user_by_username(modal.username.value)
        except:
            return

        available_string_subsets = [
            "Dog",
            "Cat",
            "Doge",
            "Horse",
            "Greece",
            "Romania",
            "America",
            "Germany",
            "ERM",
            "Electricity",
        ]

        full_string = f"ERM {' '.join([random.choice(available_string_subsets) for _ in range(6)])}"

        if msg:
            await msg.edit(
                embed=discord.Embed(
                    title="Legacy Code Verification",
                    description=f"To utilise this verification for **{user.name}**, put the following code in your Roblox account description.\n`{full_string}`",
                    color=BLANK_COLOR,
                ),
                view=(view := CompleteVerification(interaction.user)),
            )
        else:
            msg = await interaction.followup.send(
                embed=discord.Embed(
                    title="Legacy Code Verification",
                    description=f"To utilise this verification for **{user.name}**, put the following code in your Roblox account description.\n`{full_string}`",
                    color=BLANK_COLOR,
                ),
                view=(view := CompleteVerification(interaction.user)),
            )

        timeout = await view.wait()
        if timeout:
            return

        try:
            new_user = await self.bot.roblox.get_user_by_username(modal.username.value)
        except:
            return

        if full_string.lower() in new_user.description.lower():
            await self.bot.pending_oauth2.db.delete_one(
                {"discord_id": interaction.user.id}
            )
            await self.bot.oauth2_users.db.insert_one(
                {"roblox_id": new_user.id, "discord_id": interaction.user.id}
            )

            self.mode = "Code"
            self.username = new_user.name
            await msg.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Successfully Linked",
                    description=f"You have been successfully linked to **{new_user.name}**.",
                    color=GREEN_COLOR,
                ),
                view=None
            )
        else:
            await msg.edit(
                embed=discord.Embed(
                    title="Not Linked",
                    description="You did not include the code in your description. Please try again later.",
                    color=BLANK_COLOR,
                ),
                view=None,
            )