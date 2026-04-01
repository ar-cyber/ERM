import discord, typing
from .CustomModals import CustomModal, CustomModalView
from .Toolkits import ConditionCreationToolkit
from utils.utils import generator
from .Selects import RoleSelect
import string
from utils.constants import BLANK_COLOR, GREEN_COLOR
from bson import ObjectId
import datetime
from utils.timestamp import td_format


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



class ManageActions(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.bot = bot
        self.user_id = user_id
        self.modal: typing.Union[None, CustomModal] = None
        self.toolkit: typing.Optional[ActionCreationToolkit] = None

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Create an Action",
                [
                    (
                        "name",
                        discord.ui.TextInput(
                            label="Name",
                            placeholder="Action Name",
                            required=True,
                        ),
                    )
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            self.value = "create"
            self.toolkit = ActionCreationToolkit(
                self.bot, self.modal.name.value, self.user_id
            )
            embed = discord.Embed(
                title="Create an Action",
                description="Using this panel, you can assign integrations to occur when you execute your action. These can affect your ER:LC servers, execute custom commands, and more. These actions will only run when you run `/actions execute` with your action.\n\n**On Execution:**\n > No Integrations",
                color=BLANK_COLOR,
            )
            await interaction.message.edit(embed=embed, view=self.toolkit)
            timeout = await self.toolkit.wait()
            if timeout:
                return
            await interaction.message.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Successfully Added",
                    description="I have successfully added this action.",
                    color=GREEN_COLOR,
                ),
                view=None,
            )
            self.toolkit.action_data["_id"] = ObjectId()
            await self.bot.actions.insert(self.toolkit.action_data)
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.secondary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Edit an Action",
                [
                    (
                        "name",
                        discord.ui.TextInput(
                            label="ID",
                            placeholder="Action ID",
                            required=True,
                        ),
                    )
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            actions = [
                i
                async for i in self.bot.actions.db.find({"Guild": interaction.guild.id})
            ]
            selected_action = None
            for item in actions:
                if item["ActionID"] == int(self.modal.name.value):
                    selected_action = item
                    break
            else:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Not Found",
                        description="I could not find an action with that ID.",
                        color=BLANK_COLOR,
                    ),
                    ephemeral=True,
                )

            self.toolkit = ActionCreationToolkit(
                self.bot, self.modal.name.value, self.user_id
            )
            self.toolkit.action_data = selected_action
            embed = discord.Embed(
                title="Edit an Action",
                description="Using this panel, you can assign integrations to occur when you execute your action. These can affect your ER:LC servers, execute custom commands, and more. These actions will only run when you run `/actions execute` with your action.\n\n**On Execution:**\n ",
                color=BLANK_COLOR,
            )
            embed.description += "\n".join(
                [
                    f'> **{i["IntegrationName"]}{":** {}".format(i["ExtraInformation"]) if i["ExtraInformation"] is not None else "**"}'
                    for i in selected_action["Integrations"]
                ]
            )
            embed.description += "\n> *New Integration*"
            if len(selected_action.get("Conditions", []) or []) != 0:
                embed.add_field(
                    name="Conditions",
                    value="\n".join(
                        [
                            f"> **{('`{}`'.format(item.get('LogicGate', '')) + ' ') if item.get('LogicGate') else ''}{item['Variable']}** `{item['Operation']}` {item['Value']}"
                            for item in selected_action["Conditions"]
                        ]
                    ),
                    inline=False,
                )
                embed.add_field(
                    name="Execution Interval",
                    value=td_format(
                        datetime.timedelta(
                            seconds=selected_action.get(
                                "ConditionExecutionInterval", 300
                            )
                        )
                    ),
                    inline=False,
                )
            await interaction.message.edit(embed=embed, view=self.toolkit)
            timeout = await self.toolkit.wait()
            if timeout:
                return
            await interaction.message.edit(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Successfully Edited",
                    description="I have successfully edited this action.",
                    color=GREEN_COLOR,
                ),
                view=None,
            )

            await self.bot.actions.update_by_id(self.toolkit.action_data)
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:
            self.modal = CustomModal(
                f"Delete an Action",
                [
                    (
                        "id_value",
                        discord.ui.TextInput(
                            label="ID",
                            placeholder="Action ID",
                            required=True,
                        ),
                    ),
                ],
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            await self.bot.actions.db.delete_one(
                {"ActionID": int(self.modal.id_value.value)}
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Deleted Action",
                    description="Action has been deleted successfully.",
                    color=GREEN_COLOR,
                )
            )

        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )


class RDMActions(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Mark as Justified", style=discord.ButtonStyle.success)
    async def mark_as_justified(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            (
                modal := CustomModal(
                    "Reason",
                    [
                        (
                            "reason",
                            discord.ui.TextInput(
                                label="Reason",
                                placeholder="e.g. Event, Purge, etc.",
                                style=discord.TextStyle.long,
                            ),
                        )
                    ],
                    {"thinking": False},
                )
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        await interaction.message.edit(
            embed=interaction.message.embeds[0].add_field(
                name="Justification",
                value=f"> {modal.reason.value}\n- {interaction.user.mention}",
            ),
            view=self.clear_items(),
        )

    @discord.ui.button(label="Jail Player", style=discord.ButtonStyle.secondary)
    async def jail_player(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join([i if i in "1234567890" else "" for i in user_id])
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":kick {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Jailed Abuser",
                    description="This command has been sent to the server. They should now be jailed in the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(
        label="Kick Player",
        style=discord.ButtonStyle.secondary,
    )
    async def kick_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join([i if i in "1234567890" else "" for i in user_id])
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":kick {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Kicked Player",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(
        label="Ban Player",
        style=discord.ButtonStyle.secondary,
    )
    async def ban_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join([i if i in "1234567890" else "" for i in user_id])
        await interaction.response.defer(ephemeral=True, thinking=False)
        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":ban {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Banned Player",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )


class GameSecurityActions(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    def enable_reflective_action(self):
        # enables the button that allows for unbanning all affected users
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.label == "Unban Affected Players":
                    item.disabled = False

    @discord.ui.button(label="Mark as Justified", style=discord.ButtonStyle.success)
    async def mark_as_justified(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            (
                modal := CustomModal(
                    "Reason",
                    [
                        (
                            "reason",
                            discord.ui.TextInput(
                                label="Reason",
                                placeholder="e.g. SSD, permitted by owners, etc.",
                                style=discord.TextStyle.long,
                            ),
                        )
                    ],
                    {"thinking": False},
                )
            )
        )
        timeout = await modal.wait()
        if timeout:
            return

        await interaction.message.edit(
            embed=interaction.message.embeds[0].add_field(
                name="Justification",
                value=f"> {modal.reason.value}\n- {interaction.user.mention}",
            ),
            view=self.clear_items(),
        )

    @discord.ui.button(
        label="Unadmin Staff Member", style=discord.ButtonStyle.secondary
    )
    async def unadmin_staff_member(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")

        user_id = "".join(filter(str.isdigit, user_id))
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":unadmin {user_id}"
        )
        cr_2 = await bot.prc_api.run_command(interaction.guild.id, f":unmod {user_id}")

        for item in self.children:
            item.disabled = False
        await interaction.message.edit(view=self)

        if command_response[0] == 200 and cr_2[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Revoked Permissions",
                    description="This command has been sent to the server. Their permissions should now be removed.",
                    color=GREEN_COLOR,
                ),
                ephemeral=True,
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

    @discord.ui.button(
        label="Unban Affected Players",
        style=discord.ButtonStyle.secondary,
        row=0,
        disabled=False,
    )
    async def unban_affected_players(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[1]

        users_ids = []
        affected_players = [
            i.strip() for i in field1.value.split("]:**")[1].split("\n")[0].split(", ")
        ]
        users = [
            await bot.roblox.get_user_by_username(item) for item in affected_players
        ]
        for item in users:
            if item is not None:
                users_ids.append(str(item.id))

        await interaction.response.defer(ephemeral=True, thinking=False)
        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":unban {','.join(users_ids)}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Unbanned Affected Players",
                    description=f"This command has been sent to the server.\n\n-# **Command Executed:** `:unban {','.join(users_ids)}`",
                    color=GREEN_COLOR,
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description=f"This command has not been executed successfully.\n\n-# **Attempted Command:** `:unban {','.join(users_ids)}`",
                    color=BLANK_COLOR,
                )
            )

    @discord.ui.button(
        label="Kick Abuser", style=discord.ButtonStyle.secondary, row=1, disabled=True
    )
    async def kick_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join(filter(str.isdigit, user_id))
        await interaction.response.defer(ephemeral=True, thinking=False)

        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":kick {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Kicked Abuser",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                )
            )

    @discord.ui.button(
        label="Ban Abuser", style=discord.ButtonStyle.secondary, row=1, disabled=True
    )
    async def ban_abuser(
        self, interaction: discord.Interaction, button: discord.ui.View
    ):
        bot = self.bot
        guild = interaction.guild
        field1 = interaction.message.embeds[0].fields[0]
        user_id = field1.value.split("**User ID:** ")[1].split("\n")
        user_id = "".join(filter(str.isdigit, user_id))
        await interaction.response.defer(ephemeral=True, thinking=False)
        command_response = await bot.prc_api.run_command(
            interaction.guild.id, f":ban {user_id}"
        )

        if command_response[0] == 200:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Banned Abuser",
                    description="This command has been sent to the server. They should now be removed from the server.",
                    color=GREEN_COLOR,
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                )
            )

