import discord, typing
from utils.utils import generalised_interaction_check_failure
from utils.constants import BLANK_COLOR



class RoleSelectFinish(discord.ui.Button):
    def __init__(self, user_id: int, select_menu: discord.ui.RoleSelect):
        self.user_id = user_id
        self.menu = select_menu
        super().__init__(label="Finish", style=discord.ButtonStyle.success)
    async def callback(self, interaction: discord.Interaction):
        select = self.menu

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.value = select.values
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
class BulkRoleSelectFinish(discord.ui.Button):
    def __init__(self, user_id: int, select_menu: typing.List[discord.ui.RoleSelect]):
        self.user_id = user_id
        self.menus = select_menu
        super().__init__(label="Finish", style=discord.ButtonStyle.success)
    async def callback(self, interaction: discord.Interaction):
        values = [select.values for select in self.menus]

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.values = values
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

class RoleSelect(discord.ui.View):
    def __init__(self, user_id, **kwargs):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.limit = 25

        for key, value in kwargs.items():
            if key == "limit":
                self.limit = value

        if self.limit > 1:
            self.placeholder = "Select roles"
        else:
            self.placeholder = "Select a role"

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(cls=discord.ui.RoleSelect)
    async def role_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.RoleSelect):
                select = child

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.value = select.values
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

class SimpleRoleSelect(discord.ui.RoleSelect):
    def __init__(self, limit, placeholder:str|None=None, **kwargs):
        if not placeholder:
            placeholder = "Select Roles" if limit > 1 else "Select a Role"
        super().__init__(placeholder=placeholder, max_values=limit, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
class SimpleTextChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, limit, **kwargs):
        super().__init__(placeholder="Select Channels" if limit > 1 else "Select a Channel", max_values=limit, channel_types=[discord.ChannelType.text], **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

class ExpandedRoleSelect(discord.ui.View):
    def __init__(self, user_id, **kwargs):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.limit = 25

        for key, value in kwargs.items():
            if key == "limit":
                self.limit = value

        if self.limit > 1:
            self.placeholder = "Select roles"
        else:
            self.placeholder = "Select a role"

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(cls=discord.ui.RoleSelect, row=0)
    async def role_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, row=3)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        selects = []
        for child in self.children:
            if isinstance(child, discord.ui.RoleSelect):
                selects.append(child)

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            value_list = [s.values for s in selects]
            new_list = []
            for list_of_values in value_list:
                for value in list_of_values:
                    if value not in new_list:
                        new_list.append(value)
            self.value = new_list
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

    @discord.ui.button(
        label="I have more than 25 roles", style=discord.ButtonStyle.secondary, row=4
    )
    async def expand(self, interaction: discord.Interaction, button: discord.ui.Button):
        for i in self.children:
            # # print(t(t(t(t(i)
            if isinstance(i, discord.ui.RoleSelect):
                for value in range(1, 3):
                    # # print(t(t(t(t(value)
                    instance = discord.ui.RoleSelect(
                        row=value, placeholder="Select roles", max_values=25
                    )
                    # # print(t(t(t(t('?')
                    # async def callback(interaction: discord.Interaction, select: discord.ui.Select):
                    #     await interaction.response.defer()

                    instance.callback = i.callback
                    # # print(t(t(t(t('*')
                    self.add_item(instance)
                    # # print(t(t(t(t('!')
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()


class UserSelect(discord.ui.View):
    def __init__(self, user_id, **kwargs):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.limit = 25

        for key, value in kwargs.items():
            if key == "limit":
                self.limit = value

        if self.limit > 1:
            self.placeholder = "Select users"
        else:
            self.placeholder = "Select a user"

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(cls=discord.ui.UserSelect)
    async def user_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.UserSelect):
                select = child

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.value = select.values
            self.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)


class VoiceChannelSelect(discord.ui.View):
    def __init__(self, user_id, **kwargs):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.limit = 25

        for key, value in kwargs.items():
            if key == "limit":
                self.limit = value

        if self.limit > 1:
            self.placeholder = "Select channels"
        else:
            self.placeholder = "Select a channel"

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.voice]
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.ChannelSelect):
                select = child

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.value = select.values
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


class ChannelSelect(discord.ui.View):
    def __init__(self, user_id, **kwargs):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id
        self.limit = 25

        for key, value in kwargs.items():
            if key == "limit":
                self.limit = value

        if self.limit > 1:
            self.placeholder = "Select channels"
        else:
            self.placeholder = "Select a channel"

        for child in self.children:
            child.placeholder = self.placeholder
            child.max_values = self.limit
            child.min_values = 1

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text]
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await interaction.response.defer()

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, row=2)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if isinstance(child, discord.ui.ChannelSelect):
                select = child

        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.value = select.values
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

class CustomSelectMenu(discord.ui.View):
    def __init__(self, user_id, options: list, limit: typing.Optional[int] = 1):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

        self.add_item(CustomDropdown(self.user_id, options, limit))

class CustomDropdown(discord.ui.Select):
    def __init__(self, user_id, options: list, limit=1):
        self.user_id = user_id
        optionList = []

        for option in options:
            if isinstance(option, str):
                optionList.append(
                    discord.SelectOption(
                        label=option.replace("_", " ").title(), value=option
                    )
                )
            elif isinstance(option, discord.SelectOption):
                optionList.append(option)

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option",
            min_values=1,
            max_values=limit,
            options=optionList,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            if len(self.values) == 1:
                self.view.value = self.values[0]
            else:
                self.view.value = self.values
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
class CustomDropdownInt(discord.ui.Select):
    def __init__(self, options: list, limit=1):
        optionList = []

        for option in options:
            if isinstance(option, str):
                optionList.append(
                    discord.SelectOption(
                        label=option.replace("_", " ").title(), value=option
                    )
                )
            elif isinstance(option, discord.SelectOption):
                optionList.append(option)

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option",
            min_values=1,
            max_values=limit,
            options=optionList,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()




class MultiDropdown(discord.ui.Select):
    def __init__(self, user_id, options: list):
        self.user_id = user_id
        optionList = []

        for option in options:
            if isinstance(option, str):
                optionList.append(
                    discord.SelectOption(
                        label=option.replace("_", " ").title(), value=option
                    )
                )
            elif isinstance(option, discord.SelectOption):
                optionList.append(option)

        # # # # print(t(t(t(t(optionList)

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option",
            max_values=len(optionList),
            options=optionList,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            if len(self.values) == 1:
                self.view.value = self.values[0]
            else:
                self.view.value = self.values
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return


class MultiSelectMenu(discord.ui.View):
    def __init__(self, user_id, options: list):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

        self.add_item(MultiDropdown(self.user_id, options))