import discord
from selects import RoleSelect
import typing
import datetime
from custommodal import CustomModal, CustomModalView
from actions import ManageActions
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


class ActionCreationToolkit(discord.ui.View):
    def __init__(self, bot, action_name, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.bot = bot
        self.user_id = user_id
        self.action_data = {
            "ActionName": action_name,
            "ActionID": next(generator),
            "Triggers": 0,
            "Integrations": [],
            "ConditionExecutionInterval": 300,
            "Conditions": [],
            "Guild": 0,
            "LastExecuted": 0,
        }

        def return_correspondent_callback(item):
            async def unnative_callback(interaction):
                await self.native_callback(interaction, item)

            return unnative_callback

        actions = [
            "Execute Custom Command",
            "Toggle Reminder",
            "Force All Staff Off Duty",
            "Send ER:LC Command",
            "Send ER:LC Message",
            "Send ER:LC Hint",
            "Delay",
            "Add Role",
            "Remove Role",
            "Execute ERM Command"
        ]

        extras = ["Remove Last Integration"]

        for item in actions:
            button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=item)
            button.callback = return_correspondent_callback(item)
            self.add_item(button)

        button = discord.ui.Button(
            style=discord.ButtonStyle.primary, label="Access Roles"
        )
        button.callback = self.set_access_roles

        self.add_item(button)

        for item in extras:
            button = discord.ui.Button(style=discord.ButtonStyle.danger, label=item)
            button.callback = self.remove_last_integration

            self.add_item(button)

        button = discord.ui.Button(style=discord.ButtonStyle.success, label="Finish")
        button.callback = self.finish

        self.add_item(button)

    async def finish(self, interaction: discord.Interaction):
        if len(self.action_data["Integrations"]) == 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Enough Integrations",
                    description="You need at least one integration to finish this action.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        self.action_data["Guild"] = interaction.guild.id
        self.stop()

    async def remove_last_integration(self, interaction: discord.Interaction):
        if len(self.action_data["Integrations"]) == 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unable To Remove",
                    description="I was unable to remove the last integration from this action. It may be that there are no integrations.",
                    color=BLANK_COLOR
                ),
                ephemeral=True
            )
        self.action_data["Integrations"].pop(-1)
        message = interaction.message
        embed = message.embeds[-1]
        lines = embed.description.splitlines()
        lines.pop(-2)
        content = "\n".join(lines)
        embed.description = content
        await interaction.message.edit(embed=embed)
        await interaction.response.defer(thinking=False)

    async def set_access_roles(self, interaction: discord.Interaction):
        view = RoleSelect(interaction.user.id, limit=10)
        view.children[0].default_values = [
            discord.utils.get(interaction.guild.roles, id=item)
            for item in (self.action_data.get("AccessRoles", []) or [])
        ]
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Access Roles",
                description="These roles will be able to execute this action. **Usually this would be your staff role.**",
                color=BLANK_COLOR,
            ),
            view=view,
            ephemeral=True,
        )
        timeout = await view.wait()
        if timeout:
            return
        self.action_data["AccessRoles"] = [i.id for i in view.value]
        await (await interaction.original_response()).delete()

    @discord.ui.button(
        label="Change Conditions",
        style=discord.ButtonStyle.primary,
        row=2,
    )
    async def add_condition(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Change Conditions",
            description="Conditions are requirements that must be met for the action. When a condition is selected, the action will be activated when the condition is met. Otherwise, the action will only be executed when ran with `/actions execute`.\n\n**If ...**\n> *No Conditions*",
            color=BLANK_COLOR,
        )
        if len(self.action_data["Conditions"]) > 0:
            embed.description = embed.description.replace("> *No Conditions*", "")
            for item in self.action_data["Conditions"]:
                embed.description += f"\n> **{(('`{}`'.format(item.get('LogicGate', '').upper())) + ' ') if item.get('LogicGate', '') != '' else ''}{item['Variable']}** `{item['Operation']}` {item['Value']}"

        embed.add_field(
            name="Execution Interval",
            value=td_format(
                datetime.timedelta(
                    seconds=self.action_data["ConditionExecutionInterval"]
                )
            ),
            inline=False,
        )

        view = ConditionCreationToolkit(self.bot)
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
        timeout = await view.wait()
        if timeout:
            return
        self.action_data["Conditions"] = view.conditions
        self.action_data["ConditionExecutionInterval"] = view.execution_interval

        embed = interaction.message.embeds[-1]
        if len(view.conditions) != 0:
            embed.add_field(
                name="Conditions",
                value="\n".join(
                    [
                        f"> **{('`{}`'.format(item.get('LogicGate', '')) + ' ') if item.get('LogicGate') else ''}{item['Variable']}** `{item['Operation']}` {item['Value']}"
                        for item in view.conditions
                    ]
                ),
                inline=False,
            )
            embed.add_field(
                name="Execution Interval",
                value=td_format(datetime.timedelta(seconds=view.execution_interval)),
                inline=False,
            )
        await interaction.message.edit(embed=embed)

    async def native_callback(self, interaction: discord.Interaction, button_name):

        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
        correspondents = {
            "Execute Custom Command": 1,
            "Toggle Reminder": 1,
            "Force All Staff Off Duty": 0,
            "Send ER:LC Command": 1,
            "Send ER:LC Message": 1,
            "Send ER:LC Hint": 1,
            "Delay": 1,
            "Add Role": 1,
            "Remove Role": 1,
            "Execute ERM Command": 1,
        }
        if not correspondents[button_name]:
            msg = interaction.message
            embed = msg.embeds[-1]

            msg.embeds[-1].description = msg.embeds[-1].description.replace("No Integrations", "").replace("*New Integration*", "")
            if (
                len(f" **{button_name}**\n> *New Integration*")
                + len(msg.embeds[-1].description)
            ) > 4000:
                embed = discord.Embed(
                    title="\u200b", color=BLANK_COLOR, description="> "
                )
                embed.description += f" **{button_name}**\n> *New Integration*"
                msg.embeds.append(embed)
            else:
                embed.description += f" **{button_name}**\n> *New Integration*"
                msg.embeds[len(msg.embeds) - 1] = embed

            await interaction.message.edit(embeds=msg.embeds)

            self.action_data["Integrations"].append(
                {
                    "IntegrationName": button_name,
                    "IntegrationID": {
                        "Execute Custom Command": 0,
                        "Toggle Reminder": 1,
                        "Force All Staff Off Duty": 2,
                        "Send ER:LC Command": 3,
                        "Send ER:LC Message": 4,
                        "Send ER:LC Hint": 5,
                        "Delay": 6,
                        "Add Role": 7,
                        "Remove Role": 8,
                        "Execute ERM Command": 9
                    }[button_name],
                    "ExtraInformation": None,
                }
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Successfully Added",
                    description="I have successfully added the integration.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )

        else:
            extra_information = {
                "Execute Custom Command": ["Custom Command Name", 0],
                "Toggle Reminder": ["Reminder Name", 0],
                "Send ER:LC Command": ["Command", 1],
                "Send ER:LC Message": ["Message", 1],
                "Send ER:LC Hint": ["Hint", 1],
                "Delay": ["Time (Seconds)", 1],
                "Add Role": ["Role ID", 0],
                "Remove Role": ["Role ID", 0],
                "Execute ERM Command": ["Command (without prefix)", 1],
            }

            view = CustomModalView(
                interaction.user.id,
                "Provide Information",
                "Provide Information",
                [
                    (
                        "info",
                        discord.ui.TextInput(label=extra_information[button_name][0]),
                    )
                ],
                {"ephemeral": True},
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Extra Information",
                    description=f"**{button_name}** requires extra information, provide it by pressing the button below.",
                    color=BLANK_COLOR,
                ),
                view=view,
                ephemeral=True,
            )
            timeout = await view.wait()
            if timeout:
                return
            provided_information = view.modal.info.value
            if not provided_information:
                return
            dynamic = extra_information[button_name][1]

            async def static_validation_failure():
                await view.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Incorrect Medium",
                        description="This medium is invalid. Please try again by clicking the button on the initial embed.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )

            if not dynamic:
                if "Role" in button_name:
                    role = interaction.guild.get_role(int(provided_information))
                    if not role:
                        await static_validation_failure()
                    provided_information = int(provided_information)

                if "Reminder" in button_name:
                    # Fetch reminders

                    reminders = await self.bot.reminders.find_by_id(
                        interaction.guild.id
                    )
                    if not reminders:
                        return await static_validation_failure()

                    reminders = reminders.get("reminders", [])
                    if not reminders:
                        return await static_validation_failure()

                    for reminder in reminders:
                        if reminder["name"] == provided_information:
                            break
                    else:
                        return await static_validation_failure()

                if "Custom Command" in button_name:
                    # Fetch Custom Commands

                    custom_commands = await self.bot.custom_commands.find_by_id(
                        interaction.guild.id
                    )
                    custom_commands = (custom_commands or {}).get("commands", [])
                    if not custom_commands:
                        return await static_validation_failure()

                    for command in custom_commands:
                        if command["name"] == provided_information:
                            break
                    else:
                        return await static_validation_failure()

            if "Command (without prefix)" in button_name:
                # strip possible prefix
                provided_information = provided_information.strip()
                if provided_information[0] not in [*string.ascii_lowercase, *string.ascii_uppercase]:
                    provided_information = provided_information[1:]

            self.action_data["Integrations"].append(
                {
                    "IntegrationName": button_name,
                    "IntegrationID": {
                        "Execute Custom Command": 0,
                        "Toggle Reminder": 1,
                        "Force All Staff Off Duty": 2,
                        "Send ER:LC Command": 3,
                        "Send ER:LC Message": 4,
                        "Send ER:LC Hint": 5,
                        "Delay": 6,
                        "Add Role": 7,
                        "Remove Role": 8,
                        "Execute ERM Command": 9
                    }[button_name],
                    "ExtraInformation": provided_information,
                }
            )
            msg = interaction.message
            embed = msg.embeds[-1]
            msg.embeds[-1].description = msg.embeds[-1].description.replace("No Integrations", "").replace("*New Integration*", "")


            if (
                len(
                    f" **{button_name}:** {provided_information}\n> *New Integration*"
                )
                + len(msg.embeds[-1].description)
            ) > 4000:
                embed = discord.Embed(
                    title="\u200b", color=BLANK_COLOR, description="> "
                )
                embed.description += f" **{button_name}:** {provided_information}\n> *New Integration*"
                msg.embeds.append(embed)
            else:
                embed.description += f" **{button_name}:** {provided_information}\n> *New Integration*"
                msg.embeds[len(msg.embeds) - 1] = embed

            await interaction.message.edit(embeds=msg.embeds)
