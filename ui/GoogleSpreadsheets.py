import discord
from utils.constants import (
    BLANK_COLOR,
    GREEN_COLOR,
    SERVER_CONDITIONS as server_conditions,
    CONDITION_OPTIONS as condition_options,
)
from .CustomModals import CustomModal
import gspread, datetime, asyncio
from utils.timestamp import td_format
class RequestGoogleSpreadsheet(discord.ui.Container):
    def __init__(
        self,
        bot,
        user_id,
        config: dict,
        scopes: list,
        data: list,
        template: str,
        total_seconds: int,
        sheet_type: str = "lb",
        additional_data=None,
        label="Google Spreadsheet",
    ):
        super().__init__()
        self.bot = bot
        self.t = sheet_type if sheet_type else "lb"
        self.additional_data = additional_data if additional_data else []
        self.user_id = user_id
        self.config = config
        self.scopes = scopes
        self.data = data
        self.template = template
        self.total_seconds = total_seconds

        self.button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id="googlespreadsheet",
            )
        self.button.callback = self._handle_spreadsheet

        self.action_row = discord.ui.ActionRow(
            self.button
        )
        self.add_item(self.action_row)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            return False
        return True



    async def _handle_spreadsheet(self, interaction: discord.Interaction):

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Generating...",
                description="We are currently generating your Google Spreadsheet.",
                color=BLANK_COLOR,
            ),
            ephemeral=True
        )

        client = gspread.service_account_from_dict(self.config)
        sheet: gspread.Spreadsheet = client.copy(
            self.template, interaction.guild.name, copy_permissions=True
        )
        new_sheet = sheet.get_worksheet(0)

        try:
            new_sheet.update_cell(4, 2, f'=IMAGE("{interaction.guild.icon.url}")')
        except AttributeError:
            pass

        if self.t == "lb":
            cell_list = new_sheet.range("D13:H999")
        elif self.t == "ar":
            cell_list = new_sheet.range("D13:I999")

        try:
            new_sheet.update_cell(
                12, 1, td_format(datetime.timedelta(seconds=self.total_seconds))
            )
        except OverflowError:
            pass

        for c, n_v in zip(cell_list, self.data):
            c.value = str(n_v)

        new_sheet.update_cells(cell_list, "USER_ENTERED")

        if self.t == "ar":
            LoAs = sheet.get_worksheet(1)
            LoAs.update_cell(4, 2, f'=IMAGE("{interaction.guild.icon.url}")')
            cell_list = LoAs.range("D13:H999")

            for cell, new_value in zip(cell_list, self.additional_data):
                if isinstance(new_value, int):
                    cell.value = f"=({new_value}/ 86400 + DATE(1970, 1, 1))"
                else:
                    cell.value = str(new_value)
            LoAs.update_cells(cell_list, "USER_ENTERED")

        client.insert_permission(
            sheet.id, value=None, perm_type="anyone", role="writer"
        )

        view = GoogleSpreadsheetModification(
            self.bot, self.config, self.scopes, "Open Google Spreadsheet", sheet.url
        )
        container = discord.ui.Container(
            accent_colour=GREEN_COLOR
        ).add_item(
            discord.ui.TextDisplay(
                (
                    f"### {self.bot.emoji_controller.get_emoji('success')} Successfully generated\n"
                    "Your Google Spreadsheet has been successfully generated."
                )
            )
        ).add_item(discord.ui.Separator()).add_item(discord.ui.ActionRow(discord.ui.Button(label="Open Google Spreadsheet", url=sheet.url)))

        await interaction.edit_original_response(
            view = discord.ui.LayoutView().add_item(container)
        )

class GoogleSpreadsheetModification(discord.ui.View):
    def __init__(self, bot, config: dict, scopes: list, label: str, url: str):
        super().__init__(timeout=600.0)
        self.add_item(discord.ui.Button(label=label, url=url))
        self.bot = bot
        self.config = config
        self.scopes = scopes
        self.url = url

    @discord.ui.button(label="Request Ownership", style=discord.ButtonStyle.secondary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomModal(
            "Request Ownership",
            [
                (
                    "email",
                    discord.ui.TextInput(
                        placeholder="Email",
                        min_length=1,
                        max_length=100,
                        label="Email",
                        custom_id="email",
                    ),
                )
            ],
        )

        await interaction.response.send_modal(modal)

        timeout = await modal.wait()
        if timeout:
            return

        email = modal.email.value

        def run_gspread_transfer():
            client = gspread.service_account_from_dict(self.config)
            sheet = client.open_by_url(self.url)
            client.insert_permission(sheet.id, value=email, perm_type="user", role="writer")
            permission_id = (sheet.list_permissions())[0]["id"]
            sheet.transfer_ownership(permission_id)
            
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_gspread_transfer)

        self.remove_item(button)

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
                condition_data["Operation"] = select.values[0]
                continue

            if select.values[0] in ["and", "or"]:
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
                    condition_data["Value"] = select.values[0]
                    continue

        self.conditions.append(condition_data)
        await interaction.response.defer(thinking=False)

        await self.update_embed(interaction, False)

    '''
    @discord.ui.button(
        label="Delete Last Condition", style=discord.ButtonStyle.red, row=4
    )
    async def delete_condition(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if len(self.conditions) == 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"Not Executed ({command_response[0]})",
                    description="These commands have not been executed successfully. Try again.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
    '''
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

