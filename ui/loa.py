import discord
from .custommodal import CustomModal

from utils.utils import generalised_interaction_check_failure
from utils.constants import GREEN_COLOR, BLANK_COLOR

# idk why but because of circular imports it has to be here
async def admin_check(bot_obj, guild, member):
    guild_settings = await bot_obj.settings.find_by_id(guild.id)
    member_role_ids = [r.id for r in member.roles]
    if guild_settings:
        if "admin_role" in guild_settings["staff_management"].keys():
            if guild_settings["staff_management"]["admin_role"] != "":
                if isinstance(guild_settings["staff_management"]["admin_role"], list):
                    for role_id in guild_settings["staff_management"]["admin_role"]:
                        if role_id in member_role_ids:
                            return True
                elif isinstance(guild_settings["staff_management"]["admin_role"], int):
                    if guild_settings["staff_management"]["admin_role"] in member_role_ids:
                        return True
        if "management_role" in guild_settings["staff_management"].keys():
            if guild_settings["staff_management"]["management_role"] != "":
                if isinstance(
                    guild_settings["staff_management"]["management_role"], list
                ):
                    for role_id in guild_settings["staff_management"]["management_role"]:
                        if role_id in member_role_ids:
                            return True
                elif isinstance(
                    guild_settings["staff_management"]["management_role"], int
                ):
                    if guild_settings["staff_management"]["management_role"] in member_role_ids:
                        return True
    if member.guild_permissions.administrator:
        return True
    return False

class LOAMenu(discord.ui.View):
    def __init__(self, bot, roles, loa_roles, loa_object, user_id, code):

        super().__init__(timeout=None)
        self.value = None
        self.bot = bot
        self.loa_object = loa_object
        if isinstance(roles, list):
            self.roles = roles
        elif isinstance(roles, int):
            self.roles = [roles]
        self.loa_role = loa_roles
        self.user_id = user_id
        self.id = code

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, custom_id="loamenu:accept"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # await interaction.response.defer()
        await interaction.response.defer(ephemeral=True, thinking=True)

        # checking for admin permission as opposed to roles - property kept for legacy
        if not await admin_check(self.bot, interaction.guild, interaction.user):
            await generalised_interaction_check_failure(interaction.followup)
            return

        for item in self.children:
            item.disabled = True
            if item.label == "Accept":
                item.label = "Accepted"
            else:
                self.remove_item(item)
        s_loa = await self.bot.loas.db.find_one({
            "message_id": interaction.message.id,
            "guild_id": interaction.guild.id
        })

        s_loa["accepted"] = True
        guild = self.bot.get_guild(s_loa["guild_id"])
        try:
            user = await guild.fetch_member(s_loa["user_id"])
        except discord.NotFound:
            user = None
        if user is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find member",
                    description="I could not find the staff member which requested this Leave of Absence.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        mentionable = ""
        try:
            await user.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji_controller.get_emoji('success')} Activity Notice Accepted",
                    description=f"Your {s_loa['type']} request in **{interaction.guild.name}** was accepted!",
                    color=GREEN_COLOR,
                )
            )
        except:
            pass

        try:
            await self.bot.loas.update_by_id(s_loa)
            if isinstance(self.loa_role, int):
                role = [discord.utils.get(guild.roles, id=self.loa_role)]
            elif isinstance(self.loa_role, list):
                role = [
                    discord.utils.get(guild.roles, id=role) for role in self.loa_role
                ]

            for rl in role:
                if rl not in user.roles:
                    await user.add_roles(rl)

            self.value = True
        except discord.HTTPException:
            pass
        embed = interaction.message.embeds[0]
        embed.title = (
            f"{self.bot.emoji_controller.get_emoji('success')} {s_loa['type']} Accepted"
        )
        embed.colour = GREEN_COLOR
        embed.set_footer(text=f"Accepted by {interaction.user.name}")

        await interaction.message.edit(
            embed=embed,
            view=None,
        )

        await self.bot.views.delete_by_id(self.id)
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{self.bot.emoji_controller.get_emoji('success')} Request Accepted",
                description=f"You have successfully accepted this staff member's {s_loa['type']} Request.",
                color=GREEN_COLOR,
            )
        )
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        custom_id="loamenu:deny",
    )
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        # checking for admin permission as opposed to roles - property kept for legacy
        if not await admin_check(self.bot, interaction.guild, interaction.user):
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)
        
        for item in self.children:
            item.disabled = True

        modal = CustomModal(
            f"Reason for Denial",
            [
                (
                    "value",
                    (
                        discord.ui.TextInput(
                            label="Reason for denial",
                            placeholder="Enter a reason for denying this person's request.",
                            required=True,
                        )
                    ),
                )
            ],
        )
        await interaction.response.send_modal(modal)

        timeout = await modal.wait()
        if timeout:
            return

        reason = modal.value.value

        for item in self.children:
            item.disabled = True
            if item.label == button.label:
                item.label = "Denied"
            else:
                self.remove_item(item)
        s_loa = None

        async for loa_item in self.bot.loas.db.find(
            {"guild_id": interaction.guild.id, "message_id": interaction.message.id}
        ):
            s_loa = loa_item

        if not s_loa:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find LOA",
                    description="I could not find the activity notice associated with this menu.",
                ),
                ephemeral=True,
            )

        s_loa["denied"] = True
        s_loa["denial_reason"] = reason

        user = interaction.guild.get_member(s_loa["user_id"])
        if not user:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Could not find member",
                    description="I could not find the staff member who made this request.",
                ),
                ephemeral=True,
            )

        try:
            await user.send(
                embed=discord.Embed(
                    title="Activity Notice Denied",
                    description=f"Your {s_loa['type']} request in **{interaction.guild.name}** was denied.\n**Reason:** {reason}",
                    color=BLANK_COLOR,
                )
            )
        except:
            pass
        await self.bot.loas.update_by_id(s_loa)

        embed = interaction.message.embeds[0]
        embed.title = f"{s_loa['type']} Denied"
        embed.colour = BLANK_COLOR
        embed.set_footer(text=f"Denied by {interaction.user.name}")

        await interaction.message.edit(embed=embed, view=None)
        self.value = False
        await self.bot.views.delete_by_id(self.id)

        self.stop()


class ActivityNoticeAdministration(discord.ui.View):
    def __init__(
        self,
        bot,
        user_id: int,
        victim: int,
        guild_id: int,
        request_type: str,
        current_notice=None,
    ):
        super().__init__(timeout=900.0)
        self.user_id = user_id
        self.value = None
        self.stored_interaction = None
        self.victim = victim
        self.bot = bot
        self.guild_id = guild_id
        self.request_type = request_type
        self.current_notice = current_notice

        if self.current_notice is not None:
            self.delete_button = discord.ui.Button(
                label="Delete", style=discord.ButtonStyle.danger
            )
            self.delete_button.callback = self.delete_notice
            self.add_item(self.delete_button)

            self.end_button = discord.ui.Button(
                label="End", style=discord.ButtonStyle.secondary
            )
            self.end_button.callback = self.end_notice
            self.add_item(self.end_button)

            self.extend_button = discord.ui.Button(
                label="Extend", style=discord.ButtonStyle.primary
            )
            self.extend_button.callback = self.extend_notice
            self.add_item(self.extend_button)

    async def visual_close(self, message: discord.Message):
        for item in self.children:
            self.remove_item(item)

        await message.edit(view=self)
        await message.delete()

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

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def create_notice(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.modal = CustomModal(
            "Create Activity Notice",
            [
                ("reason", discord.ui.TextInput(label="Reason")),
                ("duration", discord.ui.TextInput(label="Duration")),
            ],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stored_interaction = self.modal.interaction
        self.value = "create"

        await self.visual_close(interaction.message)
        self.stop()

    @discord.ui.button(label="List", style=discord.ButtonStyle.secondary)
    async def list_notices(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(thinking=False, ephemeral=True)
        self.stored_interaction = interaction
        self.value = "list"

        await self.visual_close(interaction.message)
        self.stop()

    async def delete_notice(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stored_interaction = interaction
        self.value = "delete"
        await self.visual_close(interaction.message)
        self.stop()

    async def end_notice(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        self.stored_interaction = interaction
        self.value = "end"

        await self.visual_close(interaction.message)
        self.stop()

    async def extend_notice(self, interaction: discord.Interaction):
        self.modal = CustomModal(
            "Extend Activity Notice",
            [("duration", discord.ui.TextInput(label="Duration"))],
            {"ephemeral": True},
        )

        await interaction.response.send_modal(self.modal)
        await self.modal.wait()
        self.stored_interaction = self.modal.interaction
        self.value = "extend"
        await self.visual_close(interaction.message)
        self.stop()



class ActivityNoticeModification(discord.ui.View):
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

    @discord.ui.button(label="End Activity Notice", style=discord.ButtonStyle.danger)
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

    @discord.ui.button(label="Void Activity Notice", style=discord.ButtonStyle.danger)
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
