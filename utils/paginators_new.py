from copy import copy

import discord
from discord.ext import commands
import reactionmenu
import typing
from ui.Selects import CustomDropdown
from utils.constants import BLANK_COLOR
from utils.utils import generalised_interaction_check_failure


class CustomPage:
    view: typing.Optional[discord.ui.LayoutView]
    identifier: typing.Optional[str]
    containers: list[discord.ui.Container]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class SelectPagination(discord.ui.LayoutView):
    def __init__(
        self,
        bot,
        user_id: int,
        pages: list[CustomPage],
        start_at=0,
        edit_method=None,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.pages = pages
        self.user_id = user_id
        self.current_index = start_at
        self.edit_method = edit_method

        self.back_button = discord.ui.Button(
            emoji=discord.PartialEmoji.from_str(
                bot.emoji_controller.get_emoji("l_arrow")
            )
        )
        self.set_current_page = discord.ui.Button(
            label=pages[start_at].identifier or "TEMP"
        )
        self.next_button = discord.ui.Button(
            emoji=discord.PartialEmoji.from_str(
                bot.emoji_controller.get_emoji("arrow")
            )
        )
        self.end_button = discord.ui.Button(
            emoji = "<:check:1163142000271429662>"
        )

        self.back_button.callback = self._back_callback
        self.set_current_page.callback = self._set_page_callback
        self.next_button.callback = self._next_callback
        self.end_button.callback = self._end_callback
        self.nav_row = discord.ui.ActionRow(
            self.back_button,
            self.set_current_page,
            self.next_button,
            self.end_button
        )
        self.nav_container = discord.ui.Container()
        self.nav_container.add_item(self.nav_row)
        self.add_item(self.nav_container)

    def _validate_page_items(self, page_view: discord.ui.LayoutView):
        for item in page_view.children:
            if getattr(item, "default", None) is not None:
                if item.default > len(item.options):
                    item.default = 0
            elif getattr(item, "default_values", None) is not None:
                if len(item.default_values) > item.max_values:
                    item.default_values = []

    def _update_identifier_label(self, new_page: CustomPage):
        if new_page.identifier:
            self.set_current_page.label = new_page.identifier

    def _build_view(self, page: CustomPage, detach: bool=False) -> discord.ui.LayoutView:
        view = discord.ui.LayoutView(timeout=None)

        for container in getattr(page, "containers", []):
            view.add_item(container)

        page_view = getattr(page, "view", None)
        if page_view:
            self._validate_page_items(page_view)
            for item in page_view.children:
                view.add_item(item)
        if not detach:
            view.add_item(self.nav_container)

        return view

    def get_current_view(self) -> discord.ui.LayoutView:
        page = self.pages[self.current_index]
        self._update_identifier_label(page)
        return self._build_view(page)
    async def _paginate(
        self,
        interaction: discord.Interaction,
        increment_index: int,
        mode: typing.Literal["set", "increment"],
    ):
        if mode == "set":
            new_index = increment_index
        elif mode == "detach":
            new_index = self.current_index
        else:
            new_index = (self.current_index + increment_index) % len(self.pages)

        self.current_index = new_index
        new_page = self.pages[new_index]

        self._update_identifier_label(new_page)
        if not mode == "detach":
            new_view = self._build_view(new_page)
        else:
            new_view = self._build_view(new_page, detach=True)

        if self.edit_method:
            await self.edit_method(view=new_view)
        else:
            await interaction.message.edit(view=new_view)

    async def _back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._paginate(interaction, -1, "increment")

    async def _set_page_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        cont = discord.ui.Container()
        cont.add_item(
            discord.ui.TextDisplay(
                "### Change the Page\nWhat page would you like to go to?"
            )
        ).add_item(
            discord.ui.Separator()
        ).add_item(
            discord.ui.ActionRow(
                CustomDropdown(
                    self.user_id,
                    [
                        discord.SelectOption(label=page.identifier, value=str(index))
                        for index, page in enumerate(self.pages)
                    ],
                )
            )
        )

        msg = await interaction.followup.send(
            view=(jump_view := discord.ui.LayoutView().add_item(cont))
        )
        await jump_view.wait()

        index = int(jump_view.value or "1000")
        await msg.delete()
        if index != 1000:
            await self._paginate(interaction, index, "set")

    async def _next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._paginate(interaction, 1, "increment")

    async def _end_callback(self, interaction: discord.Interaction):
        self.remove_item(self.nav_container)
        await interaction.response.defer()
        await self._paginate(interaction, 0, "detach")
        

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            await generalised_interaction_check_failure(interaction.followup)
            return False
        else:
            return True