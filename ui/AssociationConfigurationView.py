import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR

class AssociationConfigurationView(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, associated_defaults: list):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

        for label, defaults in associated_defaults:
            use_configuration = None
            if len(defaults) == 0:
                continue
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
                        break

                    for index, option in enumerate(item.options):
                        if index != find_index:
                            option.default = False

    async def on_timeout(self) -> None:
        for i in self.children:
            i.disabled = True
        if not hasattr(self, "message") or not self.message:
            return
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