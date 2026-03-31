import discord
import typing
from utils.utils import generalised_interaction_check_failure
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
