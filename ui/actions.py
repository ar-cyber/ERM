import discord, typing
from custommodal import CustomModal
from toolkits import ActionCreationToolkit
from utils.constants import BLANK_COLOR, GREEN_COLOR
from bson import ObjectId
import datetime
from utils.timestamp import td_format

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
