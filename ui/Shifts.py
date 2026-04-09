# TODO: Rewrite to CV2 to not require the bridge for these

import discord, typing, pytz, datetime, logging, asyncio
from discord.ext import commands
from datamodels.ShiftManagement import ShiftItem
from utils.utils import generalised_interaction_check_failure, get_elapsed_time, time_converter
from utils.timestamp import td_format
from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, ORANGE_COLOR, ShiftTypeMappingToColor
from discord import Interaction
from bson import ObjectId
from .CustomModals import CustomModal

class ShiftMenuV2(discord.ui.Container):
    def __init__(
        self,
        bot: commands.Bot,
        section: discord.ui.Section,
        starting_state: typing.Literal["on", "break", "off"],
        user_id: int,
        shift_type: str,
        starting_document: dict | None = None,
        starting_container: ShiftItem | None = None,            
    ):
        super().__init__(accent_color=ShiftTypeMappingToColor[starting_state])
        self.user_id = user_id
        self.state = starting_state
        self.bot = bot
        self.shift_type = shift_type
        self.shift = starting_document
        self.contained_document = starting_container
        self.message = None

        self.on_duty_toggle_button = discord.ui.Button(
            style = discord.ButtonStyle.danger if starting_state != "on" else discord.ButtonStyle.green,
            label = "Start Shift" if starting_state == "off" else "End Shift"
        )
        self.on_duty_toggle_button.callback = self._on_shift_action

        self.state_button = discord.ui.Button(
            label = self._get_label(starting_state),
            disabled=True
        )

        self.break_button = discord.ui.Button(
            label = "Start Break" if starting_state == "break" else "End Break",
            disabled = True if starting_state == "off" else False,
        )

        self.set_buttons()

        self.actionrow = discord.ui.ActionRow(self.on_duty_toggle_button, self.state_button, self.break_button)
        self.add_item(self.actionrow)
    async def _check_break(self, contained_document: ShiftItem):  
        for break_item in contained_document.breaks:
            logging.info(
                f"Checking break: {break_item}"
            )  # Debugging log to print each break
            if (
                break_item.end_epoch == 0
            ):  # Assuming end_epoch is 0 if the break hasn't ended yet
                return break_item
                
        return False
    def set_buttons(self):
        match self.state:
            case "on":
                self.on_duty_toggle_button.label = "End Shift"
                self.on_duty_toggle_button.style = discord.ButtonStyle.red
                self.break_button.label = "Start Break"
                self.break_button.disabled = False
            case "break":
                self.break_button.label = "Resume Shift"
                self.break_button.style = discord.ButtonStyle.green
            case "end":
                self.break_button.label = "Start Break"
                self.break_button.style = discord.ButtonStyle.secondary
                self.break_button.disabled = True
                self.on_duty_toggle_button.label = "Start Shift"
                self.on_duty_toggle_button.style = discord.ButtonStyle.green
        self.state_button.label = self._get_label(self.state)     

    async def cycle_ui(self, option, message: discord.Message):
        shift = self.shift
        contained_document = self.contained_document
        if not contained_document and not shift:
            return
        uis = {
            "on": discord.ui.Section(
                discord.ui.TextDisplay(f"-# {message.guild.name}\n{self.bot.emoji_controller.get_emoji('ShiftStarted')} **Shift Started**"),
                accessory=discord.ui.Thumbnail(media=message.guild.icon.with_format("png").url)
            ).add_item(discord.ui.TextDisplay((
                    "### Current Shift\n"
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                )),
            ),
            "off": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                color=RED_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Shift Overview",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Ended:** <t:{int(contained_document.end_epoch or datetime.datetime.now(tz=pytz.UTC).timestamp())}:R>"
                ),
                inline=False,
            ),
        }
        if option == "break":
            current_break = None
            for break_item in contained_document.breaks:
                logging.info(
                    f"Checking break: {break_item}"
                )  # Debugging log to print each break
                if (
                    break_item.end_epoch == 0
                ):  # Assuming end_epoch is 0 if the break hasn't ended yet
                    current_break = break_item
                    break

            if current_break:
                break_start_time = (
                    f"> **Break Started:** <t:{int(current_break.start_epoch)}:R>\n"
                )
            else:
                break_start_time = "> **Break Started:** No ongoing break\n"

            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftBreak')} **On-Break**",
                    color=ORANGE_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Shift Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"{break_start_time}"
                        f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                )
            )
        else:
            selected_ui = uis[option]

        if not selected_ui:
            return
        self.set_buttons()
        await message.edit(embed=selected_ui, view=self)
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.user_id:
            # Refresh current data to ensure state has not changed
            current_shift = await self.bot.shift_management.get_current_shift(
                interaction.user, interaction.guild.id
            )
            self.shift = current_shift
            if self.shift:
                self.contained_document = await self.bot.shift_management.fetch_shift(
                    self.shift["_id"]
                )
            else:
                self.contained_document = None
            if self.contained_document:
                if self.contained_document.breaks:
                    if self.contained_document.breaks[-1].end_epoch == 0:
                        self.state = "break"
                    else:
                        self.state = "on"
                else:
                    self.state = "on"
            else:
                self.state = "off"
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
    
    def _get_label(self, state: str):
        match state:
            case "on":
                return "On-Duty"
            case "break":
                return "On Break"
            case "end":
                return "Off-Duty"
            case _:
                return "Unknown"

    async def _on_shift_action(self, interaction: Interaction):
        await interaction.response.defer(thinking=False)
        if self.state == "break":
            self.shift["Breaks"][-1]["EndEpoch"] = datetime.datetime.now(
                tz=pytz.UTC
            ).timestamp()
            self.shift["_id"] = self.contained_document.id
            await self.bot.shift_management.shifts.update_by_id(self.shift)
            await asyncio.sleep(1)
            self.contained_document = await self.bot.shift_management.fetch_shift(
                self.contained_document.id
            )
            await self.cycle_ui("on", interaction.message)
            self.bot.dispatch("break_end", self.contained_document.id)
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        access = True
        for item in settings.get("shift_management", {}).get("shift_types", []):
            if isinstance(item, dict):
                if item["name"] == self.shift_type:
                    access_roles = item.get("access_roles") or []
                    if len(access_roles) > 0:
                        access = False
                        for role in access_roles:
                            if role in [i.id for i in interaction.user.roles]:
                                access = True
                                break
        if not access:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Access",
                    description="You are not permitted to go on-duty as this Shift Type.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if self.state == "on" or self.state == "break":
            return await self.cycle_ui(self.state, interaction.message)

        object_id = await self.bot.shift_management.add_shift_by_user(
            interaction.user, self.shift_type, [], interaction.guild.id
        )
        self.contained_document: ShiftItem = (
            await self.bot.shift_management.fetch_shift(object_id)
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(object_id)
        await self.cycle_ui("on", interaction.message)
        self.bot.dispatch("shift_start", self.shift["_id"])
        return

class ShiftMenu(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        starting_state: typing.Literal["on", "break", "off"],
        user_id: int,
        shift_type: str,
        starting_document: dict | None = None,
        starting_container: ShiftItem | None = None,
    ):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.state = starting_state
        self.bot = bot
        self.shift_type = shift_type
        self.shift = starting_document
        self.contained_document = starting_container
        self.message = None

        self.check_buttons(self.state)

    def check_buttons(self, option: typing.Literal["on", "break", "off"]):
        if option == "on":
            buttons = ["Toggle Break", "Off-Duty"]
        elif option == "break":
            buttons = ["On-Duty", "Off-Duty"]
        else:
            buttons = ["On-Duty"]

        for item in self.children:
            if item.label not in buttons:
                item.disabled = True
            else:
                item.disabled = False

    async def interaction_check(self, interaction: Interaction, /) -> bool:

        if interaction.user.id == self.user_id:
            # Refresh current data to ensure state has not changed
            current_shift = await self.bot.shift_management.get_current_shift(
                interaction.user, interaction.guild.id
            )
            self.shift = current_shift
            if self.shift:
                self.contained_document = await self.bot.shift_management.fetch_shift(
                    self.shift["_id"]
                )
            else:
                self.contained_document = None
            if self.contained_document:
                if self.contained_document.breaks:
                    if self.contained_document.breaks[-1].end_epoch == 0:
                        self.state = "break"
                    else:
                        self.state = "on"
                else:
                    self.state = "on"
            else:
                self.state = "off"
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

    async def cycle_ui(
        self, option: typing.Literal["on", "break", "off"], message: discord.Message
    ):
        shift = self.shift
        contained_document = self.contained_document
        if not contained_document and not shift:
            return
        uis = {
            "on": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftStarted')} **Shift Started**",
                color=GREEN_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Current Shift",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                ),
                inline=False,
            ),
            "off": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                color=RED_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Shift Overview",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Ended:** <t:{int(contained_document.end_epoch or datetime.datetime.now(tz=pytz.UTC).timestamp())}:R>"
                ),
                inline=False,
            ),
        }
        if option == "break":
            current_break = None
            for break_item in contained_document.breaks:
                logging.info(
                    f"Checking break: {break_item}"
                )  # Debugging log to print each break
                if (
                    break_item.end_epoch == 0
                ):  # Assuming end_epoch is 0 if the break hasn't ended yet
                    current_break = break_item
                    break

            if current_break:
                break_start_time = (
                    f"> **Break Started:** <t:{int(current_break.start_epoch)}:R>\n"
                )
            else:
                break_start_time = "> **Break Started:** No ongoing break\n"

            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftBreak')} **On-Break**",
                    color=ORANGE_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Shift Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"{break_start_time}"
                        f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                )
            )
        else:
            selected_ui = uis[option]

        if not selected_ui:
            return
        self.check_buttons(option)
        await message.edit(embed=selected_ui, view=self)

    async def on_timeout(self) -> None:
        if not self.message:
            for item in self.children:
                item.disabled = True

            return await self.message.edit(view=self)

    @discord.ui.button(label="On-Duty", style=discord.ButtonStyle.green)
    async def on_duty_button(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer(thinking=False)
        if self.state == "break":
            self.shift["Breaks"][-1]["EndEpoch"] = datetime.datetime.now(
                tz=pytz.UTC
            ).timestamp()
            self.shift["_id"] = self.contained_document.id
            await self.bot.shift_management.shifts.update_by_id(self.shift)
            await asyncio.sleep(1)
            self.contained_document = await self.bot.shift_management.fetch_shift(
                self.contained_document.id
            )
            await self.cycle_ui("on", interaction.message)
            self.bot.dispatch("break_end", self.contained_document.id)
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        access = True
        for item in settings.get("shift_management", {}).get("shift_types", []):
            if isinstance(item, dict):
                if item["name"] == self.shift_type:
                    access_roles = item.get("access_roles") or []
                    if len(access_roles) > 0:
                        access = False
                        for role in access_roles:
                            if role in [i.id for i in interaction.user.roles]:
                                access = True
                                break
        if not access:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Access",
                    description="You are not permitted to go on-duty as this Shift Type.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if self.state == "on" or self.state == "break":
            return await self.cycle_ui(self.state, interaction.message)

        object_id = await self.bot.shift_management.add_shift_by_user(
            interaction.user, self.shift_type, [], interaction.guild.id
        )
        self.contained_document: ShiftItem = (
            await self.bot.shift_management.fetch_shift(object_id)
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(object_id)
        await self.cycle_ui("on", interaction.message)
        self.bot.dispatch("shift_start", self.shift["_id"])
        return

    @discord.ui.button(label="Toggle Break", style=discord.ButtonStyle.secondary)
    async def toggle_break_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        self.shift["Breaks"].append(
            {
                "StartEpoch": datetime.datetime.now(tz=pytz.UTC).timestamp(),
                "EndEpoch": 0,
            }
        )
        self.shift["_id"] = self.contained_document.id
        await self.bot.shift_management.shifts.update_by_id(self.shift)
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        await self.cycle_ui("break", interaction.message)
        self.bot.dispatch("break_start", self.contained_document.id)
        return

    @discord.ui.button(label="Off-Duty", style=discord.ButtonStyle.red)
    async def off_duty_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        await self.bot.shift_management.end_shift(
            self.contained_document.id, self.contained_document.guild
        )
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(
            self.contained_document.id
        )
        await self.cycle_ui("off", interaction.message)
        try:
            self.bot.dispatch("shift_end", self.contained_document.id)
        except Exception as e:
            logging.info(f"Error dispatching shift_end: {e}")
        return


class AdministratedShiftMenu(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        starting_state: typing.Literal["on", "break", "off"],
        user_id: int,
        target_id: int,
        shift_type: str,
        starting_document: dict | None = None,
        starting_container: ShiftItem | None = None,
    ):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.target_id = target_id
        self.state = starting_state
        self.bot = bot
        self.shift_type = shift_type
        self.shift = starting_document
        self.contained_document = starting_container
        self.message = None

        self.check_buttons(self.state)

    def check_buttons(self, option: typing.Literal["on", "break", "off"]):
        if option == "on":
            buttons = ["Toggle Break", "Off-Duty", "Other Options"]
        elif option == "break":
            buttons = ["On-Duty", "Off-Duty", "Other Options"]
        else:
            buttons = ["On-Duty", "Other Options"]

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.label not in buttons:
                    item.disabled = True
                else:
                    item.disabled = False

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

    async def cycle_ui(
        self,
        option: typing.Literal["on", "break", "off", "void"],
        message: discord.Message,
    ):
        shift = self.shift
        contained_document = self.contained_document
        previous_shifts = [
            i
            async for i in self.bot.shift_management.shifts.db.find(
                {
                    "UserID": self.target_id,
                    "Guild": message.guild.id,
                    "EndEpoch": {"$ne": 0},
                }
            )
        ]
        self.state = option
        if option == "void":
            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                    color=RED_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Statistics",
                    value=(
                        f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n"
                        f"> **Total Shifts:** {len(previous_shifts)}\n"
                        f"> **Average Shift Duration:** {td_format(datetime.timedelta(seconds=(sum([get_elapsed_time(item) for item in previous_shifts]).__truediv__(len(previous_shifts) or 1))))}\n"
                    ),
                    inline=False,
                )
            )
        elif option not in ["void", "break"]:
            if not contained_document:
                return
            uis = {
                "on": discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftStarted')} **Shift Started**",
                    color=GREEN_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Statistics",
                    value=(
                        f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n"
                        f"> **Total Shifts:** {len(previous_shifts)}\n"
                        f"> **Average Shift Duration:** {td_format(datetime.timedelta(seconds=(sum([get_elapsed_time(item) for item in previous_shifts]).__truediv__(len(previous_shifts) or 1))))}\n"
                    ),
                    inline=False,
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"> **Breaks:** {len(contained_document.breaks)}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                ),
                "off": discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                    color=RED_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Shift Overview",
                    value=(
                        f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"> **Breaks:** {len(contained_document.breaks)}\n"
                        f"> **Ended:** <t:{int(contained_document.end_epoch or datetime.datetime.now(tz=pytz.UTC).timestamp())}:R>"
                    ),
                    inline=False,
                ),
            }
        if option == "break":
            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftBreak')} **On-Break**",
                    color=ORANGE_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Statistics",
                    value=(
                        f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n"
                        f"> **Total Shifts:** {len(previous_shifts)}\n"
                        f"> **Average Shift Duration:** {td_format(datetime.timedelta(seconds=(sum([get_elapsed_time(item) for item in previous_shifts]).__truediv__(len(previous_shifts) or 1))))}\n"
                    ),
                    inline=False,
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Shift Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"> **Break Started:** <t:{int(contained_document.breaks[0].start_epoch)}:R>\n"
                        f"> **Breaks:** {len(contained_document.breaks)}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                )
            )
        elif option not in ["void", "break"]:
            selected_ui = uis[option]

        # if not selected_ui:
        #     return
        self.check_buttons(option)
        await message.edit(embed=selected_ui, view=self)

    async def on_timeout(self) -> None:
        if not self.message:
            for item in self.children:
                item.disabled = True

            return await self.message.edit(view=self)

    async def _manipulate_shift_time(
        self, message, op: typing.Literal["add", "subtract"], amount: int
    ):
        self.message = message
        member = await self.message.guild.fetch_member(self.target_id)
        guild = self.message.guild

        operations = {
            "add": self.bot.shift_management.add_time_to_shift,
            "subtract": self.bot.shift_management.remove_time_from_shift,
        }

        chosen_operation = operations[op]
        if self.contained_document is not None:
            check_for_update = await self.bot.shift_management.shifts.find_by_id(
                ObjectId(self.shift["_id"])
            )
            if check_for_update != self.shift:
                self.shift = check_for_update
                self.contained_document = await self.bot.shift_management.fetch_shift(
                    self.shift["_id"]
                )

        if self.contained_document is not None:
            if self.contained_document.end_epoch == 0:
                await chosen_operation(self.contained_document.id, amount)
                new_contained_document = await self.bot.shift_management.fetch_shift(
                    self.contained_document.id
                )
                self.contained_document = new_contained_document
                self.shift = await self.bot.shift_management.shifts.find_by_id(
                    self.contained_document.id
                )

                self.bot.dispatch(
                    "shift_edit",
                    self.contained_document.id,
                    "added_time" if op == "add" else "removed_time",
                    (await self.message.guild.fetch_member(self.user_id)),
                )
                return

        oid = await self.bot.shift_management.add_shift_by_user(
            member, self.shift_type, [], guild.id
        )
        await chosen_operation(oid, amount)
        await self.bot.shift_management.end_shift(oid, guild.id)
        self.contained_document = None
        self.shift = None

    @discord.ui.button(label="On-Duty", style=discord.ButtonStyle.green)
    async def on_duty_button(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer(thinking=False)
        if self.state == "break":
            self.shift["Breaks"][-1]["EndEpoch"] = datetime.datetime.now(
                tz=pytz.UTC
            ).timestamp()
            self.shift["_id"] = self.contained_document.id
            await self.bot.shift_management.shifts.update_by_id(self.shift)
            self.contained_document = await self.bot.shift_management.fetch_shift(
                self.contained_document.id
            )
            await self.cycle_ui("on", interaction.message)
            self.bot.dispatch("break_end", self.contained_document.id)
            return

        object_id = await self.bot.shift_management.add_shift_by_user(
            await interaction.guild.fetch_member(self.target_id),
            self.shift_type,
            [],
            interaction.guild.id,
        )
        self.contained_document: ShiftItem = (
            await self.bot.shift_management.fetch_shift(object_id)
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(object_id)
        await self.cycle_ui("on", interaction.message)
        self.bot.dispatch("shift_start", self.shift["_id"])
        return

    @discord.ui.button(label="Toggle Break", style=discord.ButtonStyle.secondary)
    async def toggle_break_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        self.shift["Breaks"].append(
            {
                "StartEpoch": datetime.datetime.now(tz=pytz.UTC).timestamp(),
                "EndEpoch": 0,
            }
        )
        self.shift["_id"] = self.contained_document.id
        await self.bot.shift_management.shifts.update_by_id(self.shift)
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        await self.cycle_ui("break", interaction.message)
        self.bot.dispatch("break_start", self.contained_document.id)
        return

    @discord.ui.button(label="Off-Duty", style=discord.ButtonStyle.red)
    async def off_duty_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        await self.bot.shift_management.end_shift(
            self.contained_document.id, self.contained_document.guild
        )
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(
            self.contained_document.id
        )
        await self.cycle_ui("off", interaction.message)
        self.bot.dispatch("shift_end", self.contained_document.id)
        return

    @discord.ui.select(
        placeholder="Other Options",
        options=[
            discord.SelectOption(
                label="Add Time",
                value="add",
                description="Add time to an ongoing shift.",
            ),
            discord.SelectOption(
                label="Subtract Time",
                value="subtract",
                description="Subtract time to an ongoing shift.",
            ),
            discord.SelectOption(
                label="Void shift",
                value="void",
                description="Void an ongoing shift.",
            ),
            discord.SelectOption(
                label="Clear Member Shifts",
                value="clear",
                description="Remove all shifts associated with this member.",
            ),
        ],
        row=1,
    )
    async def other_options(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        value = select.values[0]
        if value not in ["add", "subtract"]:
            await interaction.response.defer(thinking=False)
        if value == "add":
            self.modal = CustomModal(
                title="Add Time",
                options=[
                    (
                        "time",
                        discord.ui.TextInput(
                            label="Time",
                            placeholder="How much time to add to this shift?",
                        ),
                    )
                ],
                epher_args={"ephemeral": True, "thinking": False},
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            unfiltered = self.modal.time.value
            try:
                converted = time_converter(unfiltered)
            except ValueError:
                return await self.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Time",
                        description="I could not convert this time. Please try again.",
                        color=BLANK_COLOR,
                    )
                )
            except OverflowError:
                return await self.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Time",
                        description="You can't add more than 6 months in shift time.",
                        color=BLANK_COLOR,
                    )
                )

            await self._manipulate_shift_time(interaction.message, "add", converted)
            settings = await self.bot.settings.find_by_id(interaction.guild.id)
            previous_shifts = [
                i
                async for i in self.bot.shift_management.shifts.db.find(
                    {
                        "UserID": self.target_id,
                        "Guild": interaction.guild.id,
                        "EndEpoch": {"$ne": 0},
                    }
                )
            ]
            if settings.get("shift_management", {}).get("channel"):
                log_channel = interaction.guild.get_channel(
                    settings["shift_management"]["channel"]
                )
                if log_channel:
                    embed = discord.Embed(
                        title="Shift Time Added",
                        description=(
                            f"> **User:** <@{self.target_id}> \n"
                            f"> **Shift Type:** {self.shift_type}\n"
                            f"> **Time Added:** {td_format(datetime.timedelta(seconds=converted))}"
                        ),
                        color=0x2F3136,
                    )
                    embed.add_field(
                        name="Added By:", value=f"> {interaction.user.mention}"
                    )
                    embed.add_field(
                        name="New Total Shift Time:",
                        value=f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n",
                        inline=False,
                    )
                    embed.set_thumbnail(
                        url=interaction.guild.get_member(
                            self.target_id
                        ).display_avatar.url
                    )
                    await log_channel.send(embed=embed)
            await asyncio.sleep(0.02)
            # # print(t(t(t(t(self.state)
            if self.state not in ["void", "off"]:
                await self.cycle_ui(self.state, interaction.message)
            else:
                await self.cycle_ui("void", interaction.message)
        elif value == "subtract":
            self.modal = CustomModal(
                title="Subtract Time",
                options=[
                    (
                        "time",
                        discord.ui.TextInput(
                            label="Time",
                            placeholder="How much time to subtract from this shift?",
                        ),
                    )
                ],
                epher_args={"ephemeral": True, "thinking": False},
            )
            await interaction.response.send_modal(self.modal)
            await self.modal.wait()
            unfiltered = self.modal.time.value
            try:
                converted = time_converter(unfiltered)
            except ValueError:
                return await self.modal.interaction.followup.send(
                    embed=discord.Embed(
                        title="Invalid Time",
                        description="I could not convert this time. Please try again.",
                        color=BLANK_COLOR,
                    )
                )

            await self._manipulate_shift_time(
                interaction.message, "subtract", converted
            )
            settings = await self.bot.settings.find_by_id(interaction.guild.id)
            previous_shifts = [
                i
                async for i in self.bot.shift_management.shifts.db.find(
                    {
                        "UserID": self.target_id,
                        "Guild": interaction.guild.id,
                        "EndEpoch": {"$ne": 0},
                    }
                )
            ]
            if settings.get("shift_management", {}).get("channel"):
                log_channel = interaction.guild.get_channel(
                    settings["shift_management"]["channel"]
                )
                if log_channel:
                    embed = discord.Embed(
                        title="Shift Time Subtracted",
                        description=(
                            f"> **User:** <@{self.target_id}> \n"
                            f"> **Shift Type:** {self.shift_type}\n"
                            f"> **Time Subtracted:** {td_format(datetime.timedelta(seconds=converted))}"
                        ),
                        color=0x2F3136,
                    )
                    embed.add_field(
                        name="Subtracted By:", value=f"> {interaction.user.mention}"
                    )
                    embed.add_field(
                        name="New Total Shift Time:",
                        value=f"> **Total Shift Duration:** {td_format(datetime.timedelta(seconds=sum([get_elapsed_time(item) for item in previous_shifts])))}\n",
                        inline=False,
                    )
                    embed.set_thumbnail(
                        url=interaction.guild.get_member(
                            self.target_id
                        ).display_avatar.url
                    )
                    await log_channel.send(embed=embed)
            await asyncio.sleep(0.02)
            # # print(t(t(t(t(self.state)
            if self.state not in ["void", "off"]:
                await self.cycle_ui(self.state, interaction.message)
            else:
                await self.cycle_ui("void", interaction.message)

        elif value == "void":
            if not self.contained_document:
                try:
                    self.contained_document = (
                        await self.bot.shift_management.fetch_shift(self.shift["_id"])
                    )
                except TypeError:
                    return

            self.bot.dispatch(
                "shift_void", interaction.user, self.contained_document.id
            )
            await asyncio.sleep(2)
            await self.bot.shift_management.shifts.delete_by_id(
                self.contained_document.id
            )
            self.contained_document = None
            self.shift = None
            await self.cycle_ui("void", interaction.message)

        elif value == "clear":
            all_target_shifts = [
                shift
                async for shift in self.bot.shift_management.shifts.db.find(
                    {"UserID": self.target_id, "Guild": interaction.guild.id}
                )
            ]
            for item in all_target_shifts:
                await self.bot.shift_management.shifts.delete_by_id(item["_id"])
            self.shift = None
            self.contained_document = None
            await self.cycle_ui("void", interaction.message)

    def check_buttons(self, option: typing.Literal["on", "break", "off"]):
        if option == "on":
            buttons = ["Toggle Break", "Off-Duty"]
        elif option == "break":
            buttons = ["On-Duty", "Off-Duty"]
        else:
            buttons = ["On-Duty"]

        for item in self.children:
            if item.label not in buttons:
                item.disabled = True
            else:
                item.disabled = False

    async def interaction_check(self, interaction: Interaction, /) -> bool:

        if interaction.user.id == self.user_id:
            # Refresh current data to ensure state has not changed
            current_shift = await self.bot.shift_management.get_current_shift(
                interaction.user, interaction.guild.id
            )
            self.shift = current_shift
            if self.shift:
                self.contained_document = await self.bot.shift_management.fetch_shift(
                    self.shift["_id"]
                )
            else:
                self.contained_document = None
            if self.contained_document:
                if self.contained_document.breaks:
                    if self.contained_document.breaks[-1].end_epoch == 0:
                        self.state = "break"
                    else:
                        self.state = "on"
                else:
                    self.state = "on"
            else:
                self.state = "off"
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

    async def cycle_ui(
        self, option: typing.Literal["on", "break", "off"], message: discord.Message
    ):
        shift = self.shift
        contained_document = self.contained_document
        if not contained_document and not shift:
            return
        uis = {
            "on": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftStarted')} **Shift Started**",
                color=GREEN_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Current Shift",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                ),
                inline=False,
            ),
            "off": discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('ShiftEnded')} **Off-Duty**",
                color=RED_COLOR,
            )
            .set_author(
                name=message.guild.name,
                icon_url=message.guild.icon.url if message.guild.icon else "",
            )
            .add_field(
                name="Shift Overview",
                value=(
                    f"> **Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                    f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                    f"> **Ended:** <t:{int(contained_document.end_epoch or datetime.datetime.now(tz=pytz.UTC).timestamp())}:R>"
                ),
                inline=False,
            ),
        }
        if option == "break":
            current_break = None
            for break_item in contained_document.breaks:
                logging.info(
                    f"Checking break: {break_item}"
                )  # Debugging log to print each break
                if (
                    break_item.end_epoch == 0
                ):  # Assuming end_epoch is 0 if the break hasn't ended yet
                    current_break = break_item
                    break

            if current_break:
                break_start_time = (
                    f"> **Break Started:** <t:{int(current_break.start_epoch)}:R>\n"
                )
            else:
                break_start_time = "> **Break Started:** No ongoing break\n"

            selected_ui = (
                discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('ShiftBreak')} **On-Break**",
                    color=ORANGE_COLOR,
                )
                .set_author(
                    name=message.guild.name,
                    icon_url=message.guild.icon.url if message.guild.icon else "",
                )
                .add_field(
                    name="Current Shift",
                    value=(
                        f"> **Shift Started:** <t:{int(contained_document.start_epoch)}:R>\n"
                        f"{break_start_time}"
                        f"> **Breaks:** {len(self.shift['Breaks'])}\n"
                        f"> **Elapsed Time:** {td_format(datetime.timedelta(seconds=get_elapsed_time(shift)))}"
                    ),
                    inline=False,
                )
            )
        else:
            selected_ui = uis[option]

        if not selected_ui:
            return
        self.check_buttons(option)
        await message.edit(embed=selected_ui, view=self)

    async def on_timeout(self) -> None:
        if not self.message:
            for item in self.children:
                item.disabled = True

            return await self.message.edit(view=self)

    @discord.ui.button(label="On-Duty", style=discord.ButtonStyle.green)
    async def on_duty_button(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer(thinking=False)
        if self.state == "break":
            self.shift["Breaks"][-1]["EndEpoch"] = datetime.datetime.now(
                tz=pytz.UTC
            ).timestamp()
            self.shift["_id"] = self.contained_document.id
            await self.bot.shift_management.shifts.update_by_id(self.shift)
            await asyncio.sleep(1)
            self.contained_document = await self.bot.shift_management.fetch_shift(
                self.contained_document.id
            )
            await self.cycle_ui("on", interaction.message)
            self.bot.dispatch("break_end", self.contained_document.id)
            return

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        access = True
        for item in settings.get("shift_management", {}).get("shift_types", []):
            if isinstance(item, dict):
                if item["name"] == self.shift_type:
                    access_roles = item.get("access_roles") or []
                    if len(access_roles) > 0:
                        access = False
                        for role in access_roles:
                            if role in [i.id for i in interaction.user.roles]:
                                access = True
                                break
        if not access:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Access",
                    description="You are not permitted to go on-duty as this Shift Type.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if self.state == "on" or self.state == "break":
            return await self.cycle_ui(self.state, interaction.message)

        object_id = await self.bot.shift_management.add_shift_by_user(
            interaction.user, self.shift_type, [], interaction.guild.id
        )
        self.contained_document: ShiftItem = (
            await self.bot.shift_management.fetch_shift(object_id)
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(object_id)
        await self.cycle_ui("on", interaction.message)
        self.bot.dispatch("shift_start", self.shift["_id"])
        return

    @discord.ui.button(label="Toggle Break", style=discord.ButtonStyle.secondary)
    async def toggle_break_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        self.shift["Breaks"].append(
            {
                "StartEpoch": datetime.datetime.now(tz=pytz.UTC).timestamp(),
                "EndEpoch": 0,
            }
        )
        self.shift["_id"] = self.contained_document.id
        await self.bot.shift_management.shifts.update_by_id(self.shift)
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        await self.cycle_ui("break", interaction.message)
        self.bot.dispatch("break_start", self.contained_document.id)
        return

    @discord.ui.button(label="Off-Duty", style=discord.ButtonStyle.red)
    async def off_duty_button(
        self, interaction: discord.Interaction, _: discord.Button
    ):
        await interaction.response.defer(thinking=False)
        await self.bot.shift_management.end_shift(
            self.contained_document.id, self.contained_document.guild
        )
        self.contained_document = await self.bot.shift_management.fetch_shift(
            self.contained_document.id
        )
        self.shift = await self.bot.shift_management.shifts.find_by_id(
            self.contained_document.id
        )
        await self.cycle_ui("off", interaction.message)
        try:
            self.bot.dispatch("shift_end", self.contained_document.id)
        except Exception as e:
            logging.info(f"Error dispatching shift_end: {e}")
        return

class ShiftTypeManagement(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=600.0)
        self.user_id = user_id
        self.value = None
        self.selected_for_deletion = None
        self.name_for_creation = None
        self.modal = None

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def _create(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        # await interaction.response.defer(thinking=False)
        self.modal = CustomModal(
            "Create Shift Type",
            [
                (
                    "shift_type_name",
                    discord.ui.TextInput(
                        label="Name", placeholder="Name of Shift Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.shift_type_name.value:
            self.name_for_creation = self.modal.shift_type_name.value
        else:
            return
        self.value = "create"
        self.stop()

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def _edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        # await interaction.response.defer(thinking=False)
        self.modal = CustomModal(
            "Edit Shift Type",
            [
                (
                    "shift_type_name",
                    discord.ui.TextInput(
                        label="Name", placeholder="Name of Shift Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.shift_type_name.value:
            self.name_for_creation = self.modal.shift_type_name.value
        else:
            return
        self.value = "edit"
        self.stop()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def _delete(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id not in [self.user_id]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR,
                )
            )
        self.modal = CustomModal(
            "Shift Type Deletion",
            [
                (
                    "shift_type",
                    discord.ui.TextInput(
                        label="Shift Type ID", placeholder="ID of the Shift Type"
                    ),
                )
            ],
        )
        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        if self.modal.shift_type.value:
            self.selected_for_deletion = self.modal.shift_type.value
        else:
            return
        self.value = "delete"
        self.stop()


class PartialShiftModify(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Add time (+)", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "add"
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Remove time (-)", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "remove"
        await interaction.edit_original_response(view=self)
        self.stop()


class ShiftModify(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Add time (+)", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "add"
        await interaction.edit_original_response(view=self)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label="Remove time (-)", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "remove"
        await interaction.edit_original_response(view=self)
        self.stop()

    @discord.ui.button(label="End shift", style=discord.ButtonStyle.danger)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "end"
        await interaction.edit_original_response(view=self)
        self.stop()

    @discord.ui.button(label="Void shift", style=discord.ButtonStyle.danger)
    async def void(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await generalised_interaction_check_failure(interaction.followup)
            return
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        self.value = "void"
        await interaction.edit_original_response(view=self)
        self.stop()

class ShiftTypeCreator(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        dataset: dict,
        option: typing.Literal["create", "edit"],
        preset_values: dict | None = None,
    ):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.restored_interaction = None
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
            title=f"{self.option.title()} a Shift Type",
            description=(
                f"> **Name:** {self.dataset['name']}\n"
                f"> **ID:** {self.dataset['id']}\n"
                f"> **Shift Channel:** {'<#{}>'.format(self.dataset.get('channel', None)) if self.dataset.get('channel', None) is not None else 'Not set'}\n"
                f"> **Nickname Prefix:** {self.dataset.get('nickname') or 'Not set'}\n"
                f"> **On-Duty Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('role', [])]) or 'Not set'}\n"
                f"> **Break Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('break_roles', [])]) or 'Not set'}\n"
                f"> **Access Roles:** {', '.join(['<@&{}>'.format(r) for r in self.dataset.get('access_roles', [])]) or 'Not set'}\n\n\n"
                f"Access Roles are roles that are able to freely use this Shift Type and are able to go on-duty as this Shift Type. If an access role is selected, an individual must have it to go on-duty with this Shift Type."
            ),
            color=BLANK_COLOR,
        )

        if all([self.dataset.get("channel") is not None]):
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
        cls=discord.ui.RoleSelect, placeholder="On-Duty Roles", row=0, max_values=25
    )  # changed to On-Duty Role for parity with the other select
    async def on_duty_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        # secvuln: prevention
        highest_role_pos = max([i.position for i in interaction.user.roles])
        compared_role_pos = max([role.position for role in select.values])
        if (
            interaction.user.id != interaction.guild.owner_id
            and highest_role_pos < compared_role_pos
        ):
            # we're not allowing this ...
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Security Concern",
                    description="You cannot choose an On-Duty Role that is higher than your maximum role.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            old_select = select
            select.default_values = list(
                filter(lambda x: x.position < highest_role_pos, select.values)
            )
            try:
                await self.refresh_ui(interaction.message)
            except discord.NotFound:
                await self.refresh_ui(
                    await self.restored_interaction.original_response()
                )
            return

        await interaction.response.defer()

        self.dataset["role"] = [i.id for i in select.values]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Break Roles",
        row=1,
        min_values=0,
        max_values=25,
    )  # changed to On-Duty Role for parity with the other select
    async def break_roles(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        # secvuln: prevention
        highest_role_pos = max([i.position for i in interaction.user.roles])
        compared_role_pos = max(
            [role.position for role in select.values] or [0]
        )  # safety for deselection!
        if (
            interaction.user.id != interaction.guild.owner_id
            and highest_role_pos < compared_role_pos
        ):
            # we're not allowing this ...
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Security Concern",
                    description="You cannot choose a Break Role that is higher than your maximum role.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )
            old_select = select
            select.default_values = list(
                filter(lambda x: x.position < highest_role_pos, select.values)
            )
            try:
                await self.refresh_ui(interaction.message)
            except discord.NotFound:
                await self.refresh_ui(
                    await self.restored_interaction.original_response()
                )
            return

        await interaction.response.defer()

        self.dataset["break_roles"] = [i.id for i in select.values]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Access Roles",
        row=2,
        max_values=25,
        min_values=0,
    )
    async def access_roles_select(
        self, interaction: discord.Interaction, select: discord.ui.RoleSelect
    ):
        await interaction.response.defer()

        self.dataset["access_roles"] = [i.id for i in select.values]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Shift Channel",
        row=3,
        max_values=1,
        channel_types=[discord.ChannelType.text],
    )
    async def channel_select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        await interaction.response.defer()

        self.dataset["channel"] = [i.id for i in select.values][0]
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.button(label="Edit Nickname Prefix", row=4)
    async def edit_nickname_prefix(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = CustomModal(
            "Edit Nickname Prefix",
            [
                (
                    "nickname_prefix",
                    discord.ui.TextInput(
                        label="Nickname Prefix", max_length=20, required=False
                    ),
                )
            ],
        )

        await interaction.response.send_modal(modal)
        await modal.wait()
        try:
            chosen_identifier = modal.nickname_prefix.value
        except ValueError:
            return

        if not chosen_identifier:
            return

        self.dataset["nickname"] = chosen_identifier
        try:
            await self.refresh_ui(interaction.message)
        except discord.NotFound:
            await self.refresh_ui(await self.restored_interaction.original_response())

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        self.cancelled = True
        await interaction.followup.send(
            embed=discord.Embed(
                title="Successfully cancelled",
                description="This Shift Type has not been created.",
                color=BLANK_COLOR,
            ),
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except discord.NotFound:
            await (await self.restored_interaction.original_response()).delete()
        self.stop()

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, disabled=True, row=4
    )
    async def finish(self, interaction: discord.Interaction, _: discord.Button):
        await interaction.response.defer()
        self.cancelled = False
        self.stop()
