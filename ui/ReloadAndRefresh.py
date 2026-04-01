import discord, typing, asyncio
from utils.constants import BLANK_COLOR


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
                    color=BLANK_COLOR,
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
                    color=BLANK_COLOR,
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

class ReloadButton(discord.ui.Button):
    def __init__(self, bot, user_id: int, custom_callback: typing.Callable, args: list):
        super().__init__(label="Reload",emoji="<:lastupdated:1176999148084535326>",style=discord.ButtonStyle.secondary,)
        self.bot = bot
        self.user_id = user_id
        self.custom_callback = custom_callback
        self.callback_args = args
        self.message = None

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.custom_callback(*self.callback_args)

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
                    color=BLANK_COLOR,
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

