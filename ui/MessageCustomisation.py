import discord, typing
from utils.utils import generalised_interaction_check_failure, int_invis_embed
from utils.constants import BLANK_COLOR

# Helpers
class SetTitle(discord.ui.Modal, title="Set Embed Title"):
    name = discord.ui.TextInput(
        label="Title", placeholder="Title of the embed", style=discord.TextStyle.short
    )
    url = discord.ui.TextInput(
        label="Title URL",
        placeholder="URL of the title",
        style=discord.TextStyle.short,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()

class SetContent(discord.ui.Modal, title="Set Message Content"):
    name = discord.ui.TextInput(
        label="Content",
        placeholder="Content of the message",
        max_length=2000,
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stop()


class SetDescription(discord.ui.Modal, title="Set Embed Description"):
    name = discord.ui.TextInput(
        label="Description",
        placeholder="Description of the embed",
        style=discord.TextStyle.long,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class SetColour(discord.ui.Modal, title="Set Embed Colour"):
    name = discord.ui.TextInput(
        label="Colour", placeholder="#DB514F", style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class SetImage(discord.ui.Modal, title="Set Image"):
    image = discord.ui.TextInput(
        label="Image URL", placeholder="Image URL", style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class AddField(discord.ui.Modal, title="Add Field"):
    name = discord.ui.TextInput(
        label="Field Name", placeholder="Field Name", style=discord.TextStyle.short
    )
    value = discord.ui.TextInput(
        label="Field Value", placeholder="Field Value", style=discord.TextStyle.short
    )
    inline = discord.ui.TextInput(
        label="Inline?",
        placeholder="Yes/No",
        default="Yes",
        style=discord.TextStyle.short,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class SetFooter(discord.ui.Modal, title="Set Footer"):
    name = discord.ui.TextInput(
        label="Footer Text", placeholder="Footer Text", style=discord.TextStyle.short
    )
    icon = discord.ui.TextInput(
        label="Footer Icon URL",
        placeholder="Footer Icon URL",
        default="",
        style=discord.TextStyle.short,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class SetAuthor(discord.ui.Modal, title="Set Author"):
    name = discord.ui.TextInput(
        label="Author Name", placeholder="Author Name", style=discord.TextStyle.short
    )
    url = discord.ui.TextInput(
        label="Author URL",
        placeholder="Author URL",
        default="",
        style=discord.TextStyle.short,
        required=False,
    )
    icon = discord.ui.TextInput(
        label="Author Icon URL",
        placeholder="Author Icon URL",
        default="",
        style=discord.TextStyle.short,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()


class SetThumbnail(discord.ui.Modal, title="Set Thumbnail"):
    thumbnail = discord.ui.TextInput(
        label="Thumbnail URL",
        placeholder="Thumbnail URL",
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)

        self.stop()




class MessageCustomisation(discord.ui.View):
    def __init__(self, user_id, data=None, persist=False, external=False):
        super().__init__(timeout=600.0)
        if data is None:
            data = {}
        self.persist = persist
        self.value: typing.Union[str, None] = None
        self.modal: typing.Union[discord.ui.Modal, None] = None
        self.newView: typing.Union[EmbedCustomisation, None] = None
        self.msg = None
        self.has_embeds = False
        self.sustained_interaction = None
        self.external = external
        if data != {}:
            msg = data.get("message", data)
            content = msg["content"]
            embeds = msg.get("embeds")
            if embeds != []:
                self.has_embeds = True
        self.user_id = user_id

    async def check_ability(self, message):
        if message.content or message.embeds is not None:
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

    @discord.ui.button(
        label="Set Message",
        style=discord.ButtonStyle.secondary,
    )
    async def content(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetContent()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            if self.sustained_interaction:
                await self.check_ability(
                    await self.sustained_interaction.original_response()
                )
                return await (
                    await self.sustained_interaction.original_response()
                ).edit(content=modal.name.value)
            await interaction.message.edit(content=modal.name.value)
            await self.check_ability(interaction.message)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Add Embed",
        style=discord.ButtonStyle.secondary,
    )
    async def addembed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            if len(interaction.message.embeds) > 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Limitation",
                        description="You can only have one embed per custom command message.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )

            newView = EmbedCustomisation(interaction.user.id, self)
            newView.sustained_interaction = self.sustained_interaction
            self.newView = newView

            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message

            await chosen_interaction_message.edit(
                view=newView,
                embed=discord.Embed(colour=BLANK_COLOR, description="\u200b"),
            )
            await interaction.response.defer(thinking=False)
            # await self.check_ability(chosen_interaction_message)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, disabled=True)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.msg = interaction.message
            self.newView = self
            self.value = "finish"
            if not self.external:
                await interaction.response.defer(thinking=False)
            else:
                await int_invis_embed(
                    interaction,
                    "your custom message has been saved. You can now continue with your configuration.",
                )
            if not self.persist and not self.sustained_interaction:
                await interaction.message.delete()
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)


class EmbedCustomisation(discord.ui.View):
    def __init__(self, user_id, view=None, external=False):
        super().__init__(timeout=600.0)
        self.value: typing.Union[str, None] = None
        self.modal: typing.Union[discord.ui.Modal, None] = None
        self.msg = None
        self.user_id = user_id
        self.external = external
        self.sustained_interaction = None
        if view is not None:
            self.parent_view = view
        else:
            self.parent_view = None

    async def check_ability(self, message):
        if message.content or message.embeds is not None:
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

    @discord.ui.button(
        label="Set Message",
        style=discord.ButtonStyle.secondary,
    )
    async def content(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetContent()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            await chosen_interaction_message.edit(content=modal.name.value)
            await self.check_ability(chosen_interaction_message)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Remove Embed",
        style=discord.ButtonStyle.secondary,
    )
    async def remove_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            if len(interaction.message.embeds) > 0:
                if self.parent_view is not None:
                    if self.sustained_interaction:
                        chosen_interaction_message = (
                            await self.sustained_interaction.original_response()
                        )
                    else:
                        chosen_interaction_message = interaction.message
                    await chosen_interaction_message.edit(
                        view=self.parent_view, embed=None
                    )
                    await int_invis_embed(interaction, "embed removed.", ephemeral=True)
                else:
                    newView = MessageCustomisation(interaction.user.id)
                    self.parent_view = newView
                    await interaction.message.edit(view=newView, embed=None)
                    return await int_invis_embed(
                        interaction, "embed removed.", ephemeral=True
                    )
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, disabled=True)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            for item in self.children:
                item.disabled = True
            self.msg = interaction.message
            self.value = "finish"
            if not self.external:
                await interaction.response.defer(thinking=False)
            else:
                await int_invis_embed(
                    interaction,
                    "your custom message has been created. You can now continue with your configuration.",
                )
            if not self.sustained_interaction:
                await interaction.message.edit(view=None)
            if self.parent_view is not None:
                self.parent_view.stop()
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Title",
        row=1,
        style=discord.ButtonStyle.secondary,
    )
    async def set_title(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id == self.user_id:
            modal = SetTitle()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            embed = interaction.message.embeds[0]
            embed.title = modal.name.value
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            await chosen_interaction_message.edit(embed=embed)
            await self.check_ability(chosen_interaction_message)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Description",
        row=1,
        style=discord.ButtonStyle.secondary,
    )
    async def set_description(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetDescription()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            embed = interaction.message.embeds[0]
            embed.description = modal.name.value
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            await chosen_interaction_message.edit(embed=embed)
            await self.check_ability(chosen_interaction_message)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Embed Colour",
        row=1,
        style=discord.ButtonStyle.secondary,
    )
    async def set_color(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetColour()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            embed = interaction.message.embeds[0]
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            try:
                embed.colour = modal.name.value
            except TypeError:
                try:
                    embed.colour = int(modal.name.value.replace("#", ""), 16)
                except TypeError:
                    return await interaction.response.send_message(
                        embed=discord.Embed(
                            title="Invalid Colour",
                            description="This colour is invalid.",
                            color=BLANK_COLOR,
                        ),
                        ephemeral=True,
                    )
            await chosen_interaction_message.edit(embed=embed)
            await self.check_ability(chosen_interaction_message)

        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Thumbnail",
        row=2,
        style=discord.ButtonStyle.secondary,
    )
    async def set_thumbnail(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetThumbnail()
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            embed = interaction.message.embeds[0]
            embed.set_thumbnail(url=modal.thumbnail.value)

            try:
                await chosen_interaction_message.edit(embed=embed)
            except discord.HTTPException:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Unavailable URL",
                        description="This URL is invalid or unavailable.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
            await self.check_ability(chosen_interaction_message)

        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Image",
        row=2,
        style=discord.ButtonStyle.secondary,
    )
    async def set_image(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetImage()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            embed = interaction.message.embeds[0]
            embed.set_image(url=modal.image.value)
            try:
                await chosen_interaction_message.edit(embed=embed)
            except discord.HTTPException:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Unavailable URL",
                        description="This URL is invalid or unavailable.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
            await self.check_ability(chosen_interaction_message)

        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Add Field",
        row=3,
        style=discord.ButtonStyle.secondary,
    )
    async def add_field(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = AddField()
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message

            await interaction.response.send_modal(modal)
            timeout = await modal.wait()
            if timeout:
                return
            self.modal = modal
            if len(interaction.message.embeds) == 0:
                return
            embed = interaction.message.embeds[0]
            try:
                inline = modal.inline.value
                if inline.lower() in ["yes", "y", "true"]:
                    inline = True
                elif inline.lower() in ["no", "n", "false"]:
                    inline = False
                else:
                    inline = False
                embed.add_field(
                    name=modal.name.value, value=modal.value.value, inline=inline
                )
            except AttributeError:
                return
            await chosen_interaction_message.edit(embed=embed)
            await self.check_ability(chosen_interaction_message)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Footer",
        row=3,
        style=discord.ButtonStyle.secondary,
    )
    async def set_footer(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            modal = SetFooter()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            embed = interaction.message.embeds[0]
            embed.set_footer(text=modal.name.value, icon_url=modal.icon.value)
            try:
                await chosen_interaction_message.edit(embed=embed)
            except discord.HTTPException:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Unavailable URL",
                        description="This URL is invalid or unavailable.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
            await self.check_ability(chosen_interaction_message)

        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="Set Author",
        row=3,
        style=discord.ButtonStyle.secondary,
    )
    async def set_author(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.user_id:
            modal = SetAuthor()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.modal = modal
            if self.sustained_interaction:
                chosen_interaction_message = (
                    await self.sustained_interaction.original_response()
                )
            else:
                chosen_interaction_message = interaction.message
            embed = interaction.message.embeds[0]
            embed.set_author(
                name=modal.name.value,
                url=modal.url.value,
                icon_url=modal.icon.value,
            )
            try:
                await chosen_interaction_message.edit(embed=embed)
            except discord.HTTPException:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Unavailable URL",
                        description="This URL is invalid or unavailable.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
            await self.check_ability(chosen_interaction_message)

        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
