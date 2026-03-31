import discord
from .Selects import RoleSelect
import typing
import datetime
from .CustomModals import CustomModal, CustomModalView
from utils.timestamp import td_format
from utils.constants import (
    BLANK_COLOR,
    GREEN_COLOR,
    SERVER_CONDITIONS as server_conditions,
    RELEVANT_DESCRIPTIONS as relevant_descriptions,
    CONDITION_OPTIONS as condition_options,
    OPTION_DESCRIPTIONS as option_descriptions,
)
import string
from utils.utils import (
    time_converter,
    generator
)
from discord import Interaction
class ConditionCreationToolkit(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600.0)
        self.hidden_items = []
        self.hidden_selects = []
        self.bot = bot

        self.execution_interval = 300
        self.conditions = []
        self.constant = 0

        self.select_data = {}

        self.hide_buttons()
        self.refresh_ui()

    def hide_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                self.hidden_items.append(item)
                self.remove_item(item)
            if isinstance(item, discord.ui.Select):
                if item.placeholder == "Select a logic gate":
                    self.hidden_selects.append(item)
                    self.remove_item(item)

    def refresh_ui(self, set_defaults=True):
        if len(self.hidden_selects) != 0 and len(self.conditions) != 0:
            for item in self.hidden_selects:
                item.row = 3
                self.add_item(item)
                self.hidden_selects = []

        if set_defaults:
            for item in self.children:
                if isinstance(item, discord.ui.Select):
                    item.disabled = False
                    for idx, option in enumerate(item.options):
                        option.default = option.value in item.values
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Select):
                    item._values = []

        if all(
            [
                len(i.values) != 0
                for i in list(
                    filter(
                        lambda x: isinstance(x, discord.ui.Select)
                        and x.placeholder != "Select a logic gate",
                        self.children,
                    )
                )
            ]
        ):
            for item in self.hidden_items:
                if "Value: " in item.label:
                    item.label = item.label.replace(
                        item.label.split("Value: ")[1], str(self.constant)
                    )
                self.add_item(item)
            self.hidden_items = []
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label not in [
                    "Finish",
                    "Delete Last Condition",
                ]:
                    self.hidden_items.append(item)
                    self.remove_item(item)

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if "Value: " in item.label:
                    item.label = item.label.replace(
                        item.label.split("Value: ")[1], str(self.constant)
                    )
            if isinstance(item, discord.ui.Select):
                if (
                    item.placeholder == "Select a logic gate"
                    and len(self.conditions) == 0
                ):
                    self.hidden_selects.append(item)
                    self.remove_item(item)

        return self

    async def update_embed(self, interaction: discord.Interaction, set_default=True):
        embed = discord.Embed(
            title="Change Conditions",
            description="Conditions are requirements that must be met for the action. When a condition is selected, the action will be activated when the condition is met. Otherwise, the action will only be executed when ran with `/actions execute`.\n\n**If ...**",
            color=BLANK_COLOR,
        )
        embed.add_field(
            name="Execution Interval",
            value=td_format(datetime.timedelta(seconds=self.execution_interval)),
            inline=False,
        )

        for item in self.conditions:
            embed.description += f"\n> **{(('`{}`'.format(item.get('LogicGate', '').upper())) + ' ') if item.get('LogicGate', '') != '' else ''}{item['Variable']}** `{item['Operation']}` {item['Value']}"

        if len(self.conditions) == 0:
            embed.description += f"\n> *No Conditions*"

        await interaction.edit_original_response(
            embed=embed, view=self.refresh_ui(set_default)
        )

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, row=4)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(label="Add Condition", style=discord.ButtonStyle.green, row=4)
    async def add_condition(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        condition_data = {}
        if self.constant != 0:
            condition_data["Value"] = self.constant
            self.constant = 0

        for select in list(
            filter(lambda x: isinstance(x, discord.ui.Select), self.children)
        ):
            if len(select.values) == 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Invalid Condition",
                        description="You must select all required values to populate a condition.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )  # this shouldnt be possible, but its good measure

            def set_default(option):
                option.default = False
                return True  # keep the option!

            select.options = list(filter(set_default, select.options))

            if select.values[0] in condition_options.values():
                print("op")
                condition_data["Operation"] = select.values[0]
                continue

            if select.values[0] in ["and", "or"]:
                print("logic")
                condition_data["LogicGate"] = select.values[0]
                continue

            if (
                select.values[0] in server_conditions.values()
                and condition_data.get("Variable") is None
            ):
                if "X" in select.values[0]:  # requires dynamic argument
                    condition_data["Variable"] = (
                        select.values[0] + f" {self.select_data.get(select)}"
                    )
                    continue
                print("var")
                condition_data["Variable"] = select.values[0]
                continue
            else:
                if (
                    condition_data.get("Value") is None
                ):  # check for preoccupied constant :)
                    if "X" in select.values[0]:  # requires dynamic argument
                        condition_data["Value"] = (
                            select.values[0] + f" {self.select_data.get(select)}"
                        )
                        continue
                    print("val")
                    condition_data["Value"] = select.values[0]
                    continue

        self.conditions.append(condition_data)
        await interaction.response.defer(thinking=False)

        await self.update_embed(interaction, False)

    @discord.ui.button(
        label="Delete Last Condition", style=discord.ButtonStyle.red, row=4
    )
    async def delete_condition(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if len(self.conditions) == 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Invalid Condition",
                    description="You must have at least one condition to delete.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
        self.conditions.pop()
        await interaction.response.defer(thinking=False)
        await self.update_embed(interaction)

    @discord.ui.button(
        label="Change Interval",
        style=discord.ButtonStyle.secondary,
        row=4,
        disabled=False,
    )
    async def change_interval(
        self, interaction: discord.Interaction, button: discord.ui.button
    ):
        modal = CustomModal(
            "Change Execution Interval",
            [
                (
                    "interval",
                    discord.ui.TextInput(
                        placeholder="Interval (s/m/h/d)",
                        min_length=1,
                        max_length=5,
                        label="Interval",
                    ),
                )
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(modal)
        timeout = await modal.wait()
        if timeout:
            return
        try:
            seconds = time_converter(modal.interval.value)
        except ValueError as _:
            return await modal.interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Interval",
                    description="The interval you entered is not a valid time.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        self.execution_interval = seconds
        await self.update_embed(interaction)

    @discord.ui.button(
        label="Constant Value: 0",
        style=discord.ButtonStyle.secondary,
        row=4,
        disabled=True,
    )
    async def view_constant_value(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        pass

    @discord.ui.select(
        placeholder="Select a value",
        options=[
            discord.SelectOption(
                label=key, value=value, description=relevant_descriptions[index]
            )
            for index, (key, value) in enumerate(server_conditions.items())
        ],
        max_values=1,
        min_values=0,
    )
    async def condition_select(
        self, interaction: discord.Interaction, select: discord.ui.select
    ):
        if not select.values:
            return await interaction.response.defer(thinking=False)
        if select.values[0] == "ERLC_X_InGame":
            modal = CustomModal(
                "Roblox Username",
                [
                    (
                        "roblox_username",
                        discord.ui.TextInput(
                            placeholder="e.g. builderman",
                            min_length=1,
                            max_length=30,
                            label="Roblox Username",
                            custom_id="value",
                        ),
                    )
                ],
                {"ephemeral": True},
            )
            await interaction.response.send_modal(modal)
            timeout = await modal.wait()
            if timeout:
                select._values = []
                await self.update_embed(interaction)

            roblox_username = modal.roblox_username.value
            try:
                await self.bot.roblox.get_user_by_username(roblox_username)
            except Exception as e:
                select._values = []
                await self.update_embed(interaction)
                await modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Value",
                        description="The value you entered is not a valid Roblox username.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
                return

            self.select_data[select] = roblox_username
        else:
            await interaction.response.defer(thinking=False)
        await self.update_embed(interaction)

    @discord.ui.select(
        placeholder="Select an operation",
        min_values=0,
        max_values=1,
        options=[
            discord.SelectOption(
                label=key, value=value, description=option_descriptions[index]
            )
            for index, (key, value) in enumerate(condition_options.items())
        ],
    )
    async def operation_select(
        self, interaction: discord.Interaction, select: discord.ui.select
    ):
        await interaction.response.defer(thinking=False)
        await self.update_embed(interaction)

    @discord.ui.select(
        placeholder="Select a value",
        min_values=0,
        max_values=1,
        options=[
            discord.SelectOption(
                label=key, value=value, description=relevant_descriptions[index]
            )
            for index, (key, value) in enumerate(server_conditions.items())
        ]
        + [
            discord.SelectOption(
                label="Constant Value",
                value="constant",
                description="A constant value that will be used in the condition",
            )
        ],
    )
    async def value2_select(
        self, interaction: discord.Interaction, select: discord.ui.select
    ):
        if select.values[0] == "constant":
            modal = CustomModal(
                "Constant Value",
                [
                    (
                        "constant",
                        discord.ui.TextInput(
                            placeholder="Value (must be a number)",
                            min_length=1,
                            max_length=5,
                            label="Value",
                            custom_id="value",
                        ),
                    )
                ],
                {"ephemeral": True},
            )
            await interaction.response.send_modal(modal)
            timeout = await modal.wait()
            if timeout:
                select._values = []
                await self.update_embed(interaction)
            if not modal.constant.value.strip().isdigit():
                select._values = []
                await self.update_embed(interaction)
                await modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Value",
                        description="The value you entered is not a valid number.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
                return
            self.constant = int(modal.constant.value)
        elif select.values[0] == "ERLC_X_InGame":
            modal = CustomModal(
                "Roblox Username",
                [
                    (
                        "roblox_username",
                        discord.ui.TextInput(
                            placeholder="e.g. builderman",
                            min_length=1,
                            max_length=30,
                            label="Roblox Username",
                            custom_id="value",
                        ),
                    )
                ],
                {"ephemeral": True},
            )
            await interaction.response.send_modal(modal)
            timeout = await modal.wait()
            if timeout:
                select._values = []
                await self.update_embed(interaction)

            roblox_username = modal.roblox_username.value
            try:
                await self.bot.roblox.get_user_by_username(roblox_username)
            except Exception as e:
                select._values = []
                await self.update_embed(interaction)
                await modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Value",
                        description="The value you entered is not a valid Roblox username.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
                return

            self.select_data[select] = roblox_username
        else:
            await interaction.response.defer(thinking=False)

        await self.update_embed(interaction)

    @discord.ui.select(
        placeholder="Select a logic gate",
        min_values=0,
        max_values=1,
        options=[
            discord.SelectOption(
                label="AND",
                value="and",
                description="All of the previous conditions must be met for the action to execute.",
            ),
            discord.SelectOption(
                label="OR",
                value="or",
                description="Any of the previous conditions must be met for the action to execute.",
            ),
        ],
    )
    async def logic_gate_select(
        self, interaction: discord.Interaction, select: discord.ui.select
    ):
        await interaction.response.defer(thinking=False)
        await self.update_embed(interaction)


class ERLCIntegrationToolkit(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=900)
        self.selected_option = None
        self.user_id = user_id
        self.content = None
        self.message = None

    @discord.ui.button(label="Message", style=discord.ButtonStyle.secondary)
    async def message(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            modal := CustomModal(
                "Edit Message Content",
                [
                    (
                        "msg_content",
                        discord.ui.TextInput(
                            label="Message Content", max_length=250, required=True
                        ),
                    )
                ],
                {"ephemeral": True},
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        self.content = modal.msg_content.value
        self.selected_option = "Message"
        await self.message.edit(
            embed=discord.Embed(
                title="<:success:1163149118366040106> Success!",
                description="Message integration has successfully been setup.",
                color=GREEN_COLOR,
            ),
            view=None,
        )
        self.stop()

    @discord.ui.button(label="Hint", style=discord.ButtonStyle.secondary)
    async def hint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            modal := CustomModal(
                "Edit Hint Content",
                [
                    (
                        "hint_content",
                        discord.ui.TextInput(
                            label="Hint Content", max_length=250, required=True
                        ),
                    )
                ],
                {"thinking": False},
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        self.content = modal.hint_content.value
        self.selected_option = "Hint"

        await self.message.edit(
            embed=discord.Embed(
                title="<:success:1163149118366040106> Success!",
                description="Hint integration has successfully been setup.",
                color=GREEN_COLOR,
            ),
            view=None,
        )
        self.stop()


class ReminderCreationToolkit(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        dataset: dict,
        option: typing.Literal["create", "edit"],
        preset_values: dict | None = None,
    ):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.dataset = dataset
        self.cancelled = None
        self.option = option

        for key, value in (preset_values or {}).items():
            for item in self.children:
                if isinstance(item, discord.ui.RoleSelect) or isinstance(
                    item, discord.ui.ChannelSelect
                ):
                    if item.placeholder == key:
                        item.default_values = value
                if isinstance(item, discord.ui.Button):
                    if item.label == key:
                        item.label = value["label"]
                        item.style = value["style"]

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
            title=f"{self.option.title()} a Reminder",
            description=(
                f"> **Name:** {self.dataset['name']}\n"
                f"> **ID:** {self.dataset['id']}\n"
                f"> **Channel:** {'<#{}>'.format(self.dataset.get('channel', None)) if self.dataset.get('channel', None) is not None else 'Not set'}\n"
                f"> **Completion Ability:** {self.dataset.get('completion_ability') or 'Not set'}\n"
                f"> **Mentioned Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('role', [])]) or 'Not set'}\n"
                f"> **Interval:** {td_format(datetime.timedelta(seconds=self.dataset.get('interval', 0))) or 'Not set'}"
                f"\n\n**Content:**\n{self.dataset['message']}"
            ),
            color=BLANK_COLOR,
        )

        if all(
            [
                self.dataset.get("channel") is not None,
                self.dataset.get("interval") is not None,
            ]
        ):
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
        cls=discord.ui.RoleSelect, placeholder="Mentioned Roles", row=0, max_values=25
    )
    async def mentioned_roles_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        await interaction.response.defer()

        self.dataset["role"] = [i.id for i in select.values]
        await self.refresh_ui(interaction.message)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Reminder Channel",
        row=1,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        await interaction.response.defer()

        self.dataset["channel"] = [i.id for i in select.values][0]
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Set Interval", style=discord.ButtonStyle.secondary, row=2)
    async def set_interval(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.modal = CustomModal(
            "Set Interval",
            [
                (
                    "interval",
                    discord.ui.TextInput(
                        label="Interval",
                        placeholder="The interval between each reminder. (hours/minutes/seconds/days)",
                        default=str(self.dataset.get("interval", 0)),
                        required=False,
                    ),
                )
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        try:
            new_time = time_converter(self.modal.interval.value)
        except ValueError:
            return await self.modal.interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Time",
                    description="You did not enter a valid time.",
                    color=BLANK_COLOR,
                )
            )

        self.dataset["interval"] = new_time
        await self.refresh_ui(interaction.message)

    @discord.ui.button(
        label="Edit ER:LC Integration", style=discord.ButtonStyle.secondary, row=2
    )
    async def edit_integration(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        msg = await interaction.response.send_message(
            embed=discord.Embed(
                title="Edit ER:LC Integration",
                description="Here you can edit your reminder's integrations with Emergency Response: Liberty County, such as sending an automatic message or hint on a reminder activation. **As of right now, you can only have one integration type per reminder.**",
                color=BLANK_COLOR,
            ),
            ephemeral=True,
            view=(view := ERLCIntegrationToolkit(interaction.user.id)),
        )
        view.message = await interaction.original_response()
        timeout = await view.wait()
        if timeout:
            return
        selected_integration = view.selected_option
        content = view.content

        self.dataset["integration"] = {
            "type": selected_integration,
            "content": view.content,
        }
        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Edit Content", style=discord.ButtonStyle.secondary, row=2)
    async def edit_content(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        self.modal = CustomModal(
            "Edit Content",
            [
                (
                    "content",
                    discord.ui.TextInput(
                        label="Content",
                        placeholder="The content of the reminder",
                        default=str(self.dataset.get("message", "")),
                        style=discord.TextStyle.long,
                        max_length=2000,
                        required=False,
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        content = self.modal.content.value

        self.dataset["message"] = content
        await self.refresh_ui(interaction.message)

    @discord.ui.button(
        label="Completion Ability: Disabled", style=discord.ButtonStyle.danger, row=2
    )
    async def edit_completion_ability(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        if button.label == "Completion Ability: Disabled":
            self.dataset["completion_ability"] = True
            button.label = "Completion Ability: Enabled"
            button.style = discord.ButtonStyle.green
        else:
            self.dataset["completion_ability"] = False
            button.label = "Completion Ability: Disabled"
            button.style = discord.ButtonStyle.danger

        await self.refresh_ui(interaction.message)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This reminder has not been created.",
                color=BLANK_COLOR,
            )
        )
        await interaction.message.delete()
        self.stop()

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, disabled=True, row=3
    )
    async def finish(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer()
        self.cancelled = False
        self.stop()



    def __init__(
        self,
        bot,
        sustained_interaction: Interaction,
        shift_types: list,
        auto_data: dict,
    ):
        self.bot = bot
        self.shift_types = shift_types
        self.sustained_interaction = sustained_interaction
        self.auto_data = auto_data
        super().__init__(timeout=None)
        self.toggle_button_styling()

    def toggle_button_styling(self):
        for item in self.children:
            if item.label == "Change Shift Type":
                item.disabled = (
                    True
                    if (
                        len(self.shift_types) == 0
                        and self.auto_data.get("shift_type") == "Default"
                    )
                    else False
                )

    @discord.ui.button(
        label="Toggle Automatic Shifts", style=discord.ButtonStyle.secondary
    )
    async def toggle_automatic_shifts(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.auto_data["enabled"] = not self.auto_data["enabled"]
        self.toggle_button_styling()
        embed = discord.Embed(
            title="Automatic Shifts", description="", color=BLANK_COLOR
        )
        for key, value in self.auto_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {(value or 'Default') if isinstance(value, str) else ('<:check:1163142000271429662>' if value is True else '<:xmark:1166139967920164915>')}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        await (await self.sustained_interaction.original_response()).edit(
            embed=embed, view=self
        )
        await interaction.response.defer(thinking=False)

    @discord.ui.button(
        label="Change Shift Type",
        style=discord.ButtonStyle.secondary,
        row=1,
        disabled=True,
    )
    async def change_shift_type(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            modal := CustomModal(
                "Change Shift Type",
                [("shift_type", discord.ui.TextInput(label="Shift Type"))],
                {"ephemeral": True},
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        if not modal.shift_type.value:
            return

        if modal.shift_type.value.lower() == "default":
            self.auto_data["shift_type"] = "Default"
        else:
            if (
                selected := {i["name"].lower(): i for i in self.shift_types}.get(
                    modal.shift_type.value.lower()
                )
            ) is None:
                return await modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="This Shift Type does not exist in your server.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )
            self.auto_data["shift_type"] = selected["name"]

        self.toggle_button_styling()
        embed = discord.Embed(
            title="Automatic Shifts", description="", color=BLANK_COLOR
        )
        for key, value in self.auto_data.items():
            embed.description += f"**{key.replace('_', ' ').title()}:** {(value or 'Default') if isinstance(value, str) else ('<:check:1163142000271429662>' if value is True else '<:xmark:1166139967920164915>')}\n"

        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        )
        await (await self.sustained_interaction.original_response()).edit(
            embed=embed, view=self
        )
        # await interaction.response.defer(thinking=False)

    @discord.ui.button(
        label="Finish Configuration", style=discord.ButtonStyle.success, row=2
    )
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await (await self.sustained_interaction.original_response()).delete()
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        if not sett:
            return
        if not sett.get("ERLC"):
            sett["ERLC"] = {}
        sett["ERLC"]["automatic_shifts"] = self.auto_data
        await self.bot.settings.update_by_id(sett)
