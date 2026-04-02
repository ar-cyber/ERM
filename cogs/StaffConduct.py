import datetime
import discord
import pytz
from discord.ext import commands
from erm import is_management
from menus import (
    YesNoMenu,
    AcknowledgeMenu,
    YesNoExpandedMenu,
    CustomModalView,
    MultiSelectMenu,
    ExpandedRoleSelect,
    MessageCustomisation,
    EmbedCustomisation,
    ChannelSelect,
)
from ui.Selects import CustomSelectMenu, CustomDropdown, SimpleRoleSelect, RoleSelectFinish, SimpleTextChannelSelect, BulkRoleSelectFinish, CustomDropdownInt
from ui.CustomModals import CustomModalButton
from erm import Bot
from utils.constants import base_infraction_type
from utils.autocompletes import infraction_type_autocomplete_special
import asyncio
import logging


successEmoji = "<:ERMCheck:1111089850720976906>"
pendingEmoji = "<:ERMPending:1111097561588183121>"
errorEmoji = "<:ERMClose:1111101633389146223>"
embedColour = 0xED4348


class StaffConduct(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    
    async def check_settings(self, ctx: commands.Context):
        error_text = "<:ERMClose:1111101633389146223> **{},** this server isn't setup with ERM! Please run `/setup` to setup the bot before trying to manage infractions".format(
            ctx.author.name
        )
        guild_settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not guild_settings:
            await ctx.reply(error_text)
            return -1
        # Currently only infractions are developed for this
        if guild_settings.get("infractions") is not None:
            return 1
        else:
            return 0

    @commands.hybrid_group(
        name="infraction",
        description="Manage infractions with ease!",
        extras={"category": "Staff Conduct"},
    )
    @is_management()
    async def infraction(self, ctx: commands.Context):
        pass

    @infraction.command(
        name="manage",
        description="Manage staff infractions, staff conduct, and custom integrations!",
        extras={"category": "Staff Conduct"},
    )
    @is_management()
    async def manage(self, ctx: commands.Context):
        bot = self.bot
        guild_settings = await bot.settings.find_by_id(ctx.guild.id)
        
        result = await self.check_settings(ctx)
        if result == -1:
            return
        first_time_setup = bool(not result)
        message = await ctx.reply(
            f"{pendingEmoji} **{ctx.author.name},** welcome to the set-up for **Staff Conduct**! Please wait while your experience loads.",
        )
        # I'm going to kill whoever made it so you can't edit your already made config for staff conduct. you made my life harder
        if first_time_setup:
            guild_settings["infractions"] = {"infractions": []}
            view = YesNoExpandedMenu(ctx.author.id)
            await message.edit(
                content=f"{pendingEmoji} **{ctx.author.name},** it looks like your server hasn't setup **Staff Conduct**! Do you want to run the **First-time Setup** wizard?",
                view=view,
            )
            timeout = await view.wait()
            if timeout:
                return
            if not view.value:
                await message.edit(
                    content=f"{errorEmoji} **{ctx.author.name},** I have cancelled the setup wizard for **Staff Conduct.**",
                    view=None,
                )
                return

            embed = discord.Embed(
                title="<:ERMAlert:1113237478892130324> Information", color=embedColour
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/emojis/1113210855891423302.webp?size=96&quality=lossless"
            )
            embed.add_field(
                name="<:ERMList:1111099396990435428> What is Staff Conduct?",
                value=">>> Staff Conduct is a module within ERM which allows for infractions on your Staff team. Not only does it allow for manual punishments and infractions to others to be expanded and customised, it also allows for automatic punishments for those that don't meet activity requirements, integrating with other ERM modules.",
                inline=False,
            )
            embed.add_field(
                name="<:ERMList:1111099396990435428> How does this module work?",
                value=">>> For manual punishment assignment, you make your own Infraction Types, as dictated throughout this setup wizard. You can then infract staff members by using `/infract`, which will assign that Infraction Type to the staff individual. You will be able to see all infractions that individual has received, as well as any notes or changes that have been made over the course of their staff career.",
                inline=False,
            )
            embed.add_field(
                name="<:ERMList:1111099396990435428> If I have a Strike 1/2/3 system, do I have them as separate types?",
                value=">>> You can use the infraction counting feature for ERM to count the strikes automatically!",
                inline=False,
            )
            embed.set_footer(
                text="This module is in beta, and bugs are to be expected. If you notice a problem with this module, report it via our Support server."
            )
            embed.timestamp = datetime.datetime.now()
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)

            view = AcknowledgeMenu(
                ctx.author.id, "Read the information in full before acknowledging."
            )
            await message.edit(
                embed=embed,
                view=view,
            )
            timeout = await view.wait()
            if timeout or not view.value:
                return
        while True:
            values = [
                discord.SelectOption(label = "Add Item", value = "add", emoji="<:ERMAdd:1113207792854106173>")
            ] + [discord.SelectOption(label = infraction["name"], value=infraction["name"], emoji="<:ERMArrow:1120534523181027358>") for infraction in guild_settings["infractions"]["infractions"]
            ] + [discord.SelectOption(label = "Global Settings", value = "global", emoji = "<:ERMLog:1113210855891423302>"), 
                discord.SelectOption(label = "Finish", value = "finish", emoji = successEmoji)]
            cont = discord.ui.Container()


            cont.add_item(
                discord.ui.TextDisplay(
                    (
                        "### Select an Infration Type\n"
                        "Select an option below to configure infraction types or change the global settings for **Staff Conduct**"
                    )
                )
            ).add_item(discord.ui.Separator()).add_item(
                discord.ui.ActionRow(
                    CustomDropdown(
                        ctx.author.id,
                        options=values,
                        
                    )
                )
            )
            await message.edit(
                content=None,
                view=(
                    view := discord.ui.LayoutView().add_item(cont)
                )
            )
            await view.wait()

            if view.value == "add":
                cont = discord.ui.Container()
                cont.add_item(
                    discord.ui.TextDisplay(
                    (
                        "### Create Infraction Type\n"
                        "Click the button below to configure infractions"
                    ))
                ).add_item(discord.ui.Separator())
                modal = CustomModalButton(
                    ctx.author.id,
                    "Add an Infraction Type",
                    "Add Infraction Type",
                    [
                        (
                            "type_name",
                            discord.ui.TextInput(
                                placeholder="e.g. Strike, Termination, Suspension, Blacklist",
                                label="Name of Infraction Type",
                            ),
                        )
                    ],
                )
                cont.add_item(discord.ui.ActionRow(modal))
                await message.edit(
                    content=None,
                    embed=None,
                    view=(
                        view := discord.ui.LayoutView().add_item(cont)
                    ),
                )
                await view.wait()
                if any(type["name"] == view.values[0] for type in guild_settings["infractions"]["infractions"]):
                    return await message.edit(
                        embed = discord.Embed(title = "Already exists", description=f"**{ctx.author.name},** this infraction type already exists"), view=None
                    )
                infraction_type_name = view.values[0]

                base_type = base_infraction_type
                base_type["name"] = infraction_type_name
                guild_settings["infractions"]["infractions"].append(base_type)
                await message.edit(
                    embed=discord.Embed(
                        title = "Created Infraction",
                        description=f"Created infraction type {infraction_type_name}"
                    )
                )
                continue
                
            elif view.value == "finish":
                await message.edit(
                    content=None,
                    embed=discord.Embed(title = "Finished", description="Have a great day!"),
                    view=None
                )
                return
            elif view.value == "global":
                while True:
                    cont = discord.ui.Container()
                    cont.add_item(discord.ui.TextDisplay(
                        (
                            "### Global Settings\n"
                            "Select an option below to change the global settings for **Staff Conduct**"
                        )
                    )).add_item(discord.ui.Separator())
                    cont.add_item(
                        discord.ui.ActionRow(
                            CustomDropdown(
                                ctx.author.id,
                                [
                                    discord.SelectOption(
                                        label="Infractions Manager Permission",
                                        description='Select the roles permitted to use the infractions module',
                                        emoji="<:SConductTitle:1053359821308567592>",
                                        value="manager",
                                    ),
                                    discord.SelectOption(
                                        label = "Finish",
                                        description="Finish setting up this infraction type",
                                        value = "finish",
                                        emoji = successEmoji
                                    )
                                ],
                            )
                        )
                    )
                    await message.edit(
                        embed=None,
                        view=(
                            view := discord.ui.LayoutView().add_item(cont)
                        ),
                    )
                    await view.wait()
                    match view.value:
                        case "manager":
                            cont = discord.ui.Container()
                            cont.add_item(discord.ui.TextDisplay(
                                "### Infraction Manager Roles\n"
                                "Select roles below for the roles that are allowed to use infraction manager features."
                            )).add_item(discord.ui.Separator())
                            rs = SimpleRoleSelect(limit=25, default_values=[discord.SelectDefaultValue(id=role, type=discord.SelectDefaultValueType.role) for role in guild_settings["infractions"].get("manager_roles", [])])
                            cont.add_item(
                                discord.ui.ActionRow(rs)
                            
                            ).add_item(
                                discord.ui.ActionRow(RoleSelectFinish(ctx.author.id, rs))
                            )
                            
                            await message.edit(
                                embed=None,
                                content=None,
                                view=(view := discord.ui.LayoutView().add_item(cont)),
                            )
                            await view.wait()
                            addRoleList = [role.id for role in view.value]
                            guild_settings["infractions"]["manager_roles"] = addRoleList
                        case "finish":
                            try:
                                await self.bot.settings.update(guild_settings)
                            except KeyError: # If nothing changes this loves to error out. idk why but don't ask me, probably a pymongo thing
                                guild_settings["_id"] = ctx.guild.id
                                await self.bot.settings.update(guild_settings)
                                logging.warning("_id failure")
                            await message.edit(
                                content=None,
                                view=discord.ui.LayoutView().add_item(discord.ui.Container().add_item(discord.ui.TextDisplay(f"### Submitted\nThe **Global Settings** have been submitted."))),
                                embed=None,
                            )
                            break
                            
                        
            else:
                infraction_type_name = view.value
                base_type = [type for type in guild_settings["infractions"]["infractions"] if type["name"] == infraction_type_name][0]
                

            index = guild_settings["infractions"]["infractions"].index(base_type)
            # This continuously iterates until they're done with this type. The view will probably expire before then so oh well...
            while True:
                cont = discord.ui.Container()
                cont.add_item(
                    discord.ui.TextDisplay(
                        (
                            "### Edit Infraction Type\n"
                            f"Please select from the below list to edit the infraction type `{infraction_type_name}`"
                        )
                    )
                ).add_item(discord.ui.Separator())
                cont.add_item(
                    discord.ui.ActionRow(
                        CustomDropdown(
                            ctx.author.id,
                            [
                                discord.SelectOption(
                                    label="Add Role",
                                    description='Add a role, such as a "Strike" role to the individual',
                                    emoji="<:ERMAdd:1113207792854106173>",
                                    value="add_role",
                                ),
                                discord.SelectOption(
                                    label="Remove Role",
                                    description='Remove an individual role, such as "Trained", from an individual.',
                                    emoji="<:ERMRemove:1113207777662345387>",
                                    value="remove_role",
                                ),
                                discord.SelectOption(
                                    label="Send Message in Channel",
                                    description="Send a Custom Message in a Channel",
                                    emoji="<:ERMLog:1113210855891423302>",
                                    value="send_message",
                                ),
                                discord.SelectOption(
                                    label="Escalate",
                                    description="Escalate this infraction if too many of them occur",
                                    emoji="<:ERMLog:1113210855891423302>",
                                    value="escalate",
                                ),
                                discord.SelectOption(
                                    label = "Role Counting",
                                    description="Count the number and assign diferent roles for each count!",
                                    emoji="<:ERMLog:1113210855891423302>",
                                    value="count"
                                ),
                                discord.SelectOption(
                                    label="Delete",
                                    description="Delete this infraction type",
                                    emoji=errorEmoji,
                                    value="delete",
                                ),
                                discord.SelectOption(
                                    label = "Finish",
                                    description="Finish setting up this infraction type",
                                    value = "finish",
                                    emoji = successEmoji
                                )
                            ],
                        ))
                )
                await message.edit(
                    content=None,
                    view=(
                        view := discord.ui.LayoutView().add_item(cont)
                    ),
                )

                await view.wait()

                value: list | None = None
                if isinstance(view.value, str):
                    value = view.value
                elif isinstance(view.value, list):
                    value = view.value[0]
                # WE NEED TO MAKE THESE MESSAGES MORE NOTICABLE FOR WHICH YOU PICKED
                # noticeable* 🤓
                # lol

                # Idk who's idea it was to use an if chain here but now it's match-case
                # I have to fix all of this but I can do that tomorrow
                match value:
                    case "add_role":
                        cont = discord.ui.Container()
                        cont.add_item(
                            discord.ui.TextDisplay(
                                (
                                    "### Add Roles\n"
                                    f"Please specify the roles to be added when a user receives an infraction with the type of **{infraction_type_name}**"
                                )
                            )
                        ).add_item(discord.ui.Separator())
                        rs = SimpleRoleSelect(limit=20, default_values=[discord.SelectDefaultValue(id=role, type=discord.SelectDefaultValueType.role) for role in base_type["role_changes"]["add"].get("roles", [])])
                        cont.add_item(
                            discord.ui.ActionRow(rs)
                        ).add_item(
                            discord.ui.ActionRow(RoleSelectFinish(ctx.author.id, rs))
                        )
                        await message.edit(
                            view=(view := discord.ui.LayoutView().add_item(cont))
                        )
                        await view.wait()
                        addRoleList = [role.id for role in view.value]
                        base_type["role_changes"]["add"]["roles"] = addRoleList
                    case "remove_role":  # Add to Database. I'VE ADDED IT TO DATABASE BUDDY
                        cont = discord.ui.Container()
                        cont.add_item(
                            discord.ui.TextDisplay(
                                (
                                    "### Remove Roles\n"
                                    f"Please specify the roles to be removed when a user receives an infraction with the type of **{infraction_type_name}**"
                                )
                            )
                        ).add_item(discord.ui.Separator())
                        rs = SimpleRoleSelect(limit=20, default_values=[discord.SelectDefaultValue(id=role, type=discord.SelectDefaultValueType.role) for role in base_type["role_changes"]["remove"].get("roles", [])])
                        cont.add_item(
                            discord.ui.ActionRow(rs)
                        ).add_item(
                            discord.ui.ActionRow(RoleSelectFinish(ctx.author.id, rs))
                        )
                        await message.edit(
                            content=None,
                            view=(view := discord.ui.LayoutView().add_item(cont)),
                            embed=None
                        )
                        await view.wait()
                        removeRoleList = [role.id for role in view.value]
                        base_type["role_changes"]["remove"]["roles"] = removeRoleList

                    case "send_message":
                        constant_msg_data = None
                        cont = discord.ui.Container()
                        cont.add_item(
                            discord.ui.TextDisplay((
                                "### Select Channel\n"
                                "Select the channel to send the message to"
                                )
                            )
                        ).add_item(
                            discord.ui.Separator()
                        )
                        cs = SimpleTextChannelSelect(limit=1, default_values=[discord.SelectDefaultValue(id=channel, type=discord.SelectDefaultValueType.channel) for channel in base_type["notifications"]["public"].get("channel", [])])
                        cont.add_item(
                            discord.ui.ActionRow(cs)
                        ).add_item(
                            discord.ui.ActionRow(RoleSelectFinish(ctx.author.id, cs))
                        )
                        # Get Channel(s) to Send Message To
                        await message.edit(
                            content=None, #f"{pendingEmoji} **{ctx.author.name},** please select the channel(s) you wish to send a message to upon a user receiving a **{infraction_type_name}**.",
                            view=(view := discord.ui.LayoutView().add_item(cont)),
                            embed=None
                        )
                        await view.wait()
                        base_type["notifications"]["public"]["channel"] = [view.value[0].id]
                        # Get Custom Message
                        view = MessageCustomisation(
                            ctx.author.id, persist=True, external=False
                        )
                        await message.edit(embed=discord.Embed(title='New Message',description="So I can help you, I need to you refer to the new message below."))
                        n_message: discord.Message = await message.reply(content=None, view=view, _cv2_skip=True)
                        await view.wait()
                        
                        updated_message = await ctx.channel.fetch_message(n_message.id)
                        message_data = {
                            "content": (
                                updated_message.content
                            ),
                            "embeds": [i.to_dict() for i in updated_message.embeds],
                        }
                        yesNoValue = YesNoMenu(ctx.author.id)
                        # Unfortunately we can't use CV2 for these because embeds are custom
                        await n_message.edit(
                            content=f"{pendingEmoji} **{ctx.author.name},** please confirm below that you wish to use the content shown below.\n\n{message_data['content']}",
                            embeds=[
                                discord.Embed.from_dict(i)
                                for i in message_data["embeds"]
                            ],
                            view=yesNoValue,
                            _cv2_skip=True
                        )
                        await yesNoValue.wait()
                        if yesNoValue.value:
                            constant_msg_data = message_data
                            pass
                        elif not yesNoValue.value:
                            break
                        
                        base_type["notifications"]["public"]["message_data"] = constant_msg_data
                        base_type["notifications"]["public"]["enabled"] = True
                        await n_message.delete()

                    case "escalate":
                        types = [discord.SelectOption(label = infraction["name"], value=infraction["name"], emoji="<:ERMArrow:1120534523181027358>") for infraction in guild_settings["infractions"]["infractions"]] + [discord.SelectOption(label="Back", description="Head back to the previous menu", value="back")]
                        type = infraction_type_name
                        while type == infraction_type_name:
                            await message.edit(
                                content=f"{pendingEmoji} **{ctx.author.name},** what infraction type should this escalate to?.",
                                embed=None,
                                view=(view := CustomSelectMenu(
                                    ctx.author.id,
                                    types
                                    )
                                ),)
                            
                            await view.wait()
                            type = view.value
                            if type == "back":
                                break
                            if type == infraction_type_name:
                                await message.edit(
                                    content=f"{errorEmoji} **{ctx.author.name},** an infraction type cannot escalate to the same infraction type!.",view=None
                                )
                                await asyncio.sleep(2)

                        if type == "back":
                            continue
                        await message.edit(
                            content=f"{pendingEmoji} **{ctx.author.name},** how many infractions of the infraction type you're editing should be issued for this user before it's escalated?",
                            view = (view := CustomModalView(
                                ctx.author.id,
                                "Change threshold",
                                "Enter an infraction threshold",
                                [
                                    (
                                        "threshold",
                                        discord.ui.TextInput(label="Enter the threshold as a number only", style=discord.TextStyle.short)
                                    )
                                ]
                            ))
                        )
                        await view.wait()
                        # i dont think unknown will like this :(
                        while True:
                            try:
                                threshold = int(view.modal.threshold.value)
                                break
                            except TypeError:
                                await message.edit(
                                    content=f"{errorEmoji} **{ctx.author.name},** the value you entered is not a number. How many infractions of the infraction type you're editing should be issued for this user before it's escalated?",
                                    view = (view := CustomModalView(
                                        ctx.author.id,
                                        "Change threshold",
                                        "Enter an infraction threshold",
                                        [
                                            (
                                                "threshold",
                                                discord.ui.TextInput(style=discord.TextStyle.short)
                                            )
                                        ]
                                    ))
                                )
                                await view.wait()
                        base_type["escalation"] = {
                            "threshold": threshold,
                            "next_infraction": type
                        }
                    case "count":
                        cont = discord.ui.Container()
                        cont.add_item(
                            discord.ui.TextDisplay(
                                (
                                    "### Infraction Counting\n"
                                    "With ERM, you can select up to three roles that are given at different offence counts. This allows you to assign different roles without having to create types for all of them.\n\n"
                                    "**This feature works best with escalations. Escalations __will not apply__ if the infraction is in a count**\n\n"
                                    "### Options\n"
                                    "**Enabled**: Enable the infraction counting system.\n"
                                    "**Count 1 Role**: The role to give on the first offence.\n"
                                    "**Count 2 Role**: The role to give on the second offence.\n"
                                    "**Count 3 Role**: The role to give on the third offence."
                                )
                            )
                        ).add_item(discord.ui.Separator())
                        if not base_type.get("counting"):
                            base_type["counting"] = {}
                        scont = discord.ui.Container()
                        enabled = CustomDropdownInt(
                            [discord.SelectOption(label="Enabled", description="Enable the counting system", value="yes"), discord.SelectOption(label="Disabled", description="Disabled the counting system", value="no")]
                        )
                        rs1 = SimpleRoleSelect(
                            1, placeholder="Select the first role", default_values = [discord.SelectDefaultValue(type=discord.SelectDefaultValueType.role, id=base_type.get("counting", {}).get("offence_1", 0))], 
                        )
                        rs2 = SimpleRoleSelect(
                            1, placeholder="Select the second role", default_values = [discord.SelectDefaultValue(type=discord.SelectDefaultValueType.role, id=base_type.get("counting", {}).get("offence_2", 0))], 
                        )
                        rs3 = SimpleRoleSelect(
                            1, placeholder="Select the third role", default_values = [discord.SelectDefaultValue(type=discord.SelectDefaultValueType.role, id=base_type.get("counting", {}).get("offence_3", 0))], 
                        )
                        scont.add_item(
                            discord.ui.ActionRow(
                                enabled
                            )
                        )
                        scont.add_item(
                            discord.ui.ActionRow(
                                rs1
                            )
                        ).add_item(
                            discord.ui.ActionRow(
                                rs2
                            )
                        ).add_item(
                            discord.ui.ActionRow(
                                rs3
                            )
                        ).add_item(
                            discord.ui.ActionRow(
                                BulkRoleSelectFinish(ctx.author.id, [enabled, rs1, rs2, rs3])
                            )
                        )
                        await message.edit(
                            view=(
                                view := discord.ui.LayoutView(timeout=300).add_item(cont).add_item(scont)
                            )
                        )

                        await view.wait()
                        enabled, r1, r2, r3 = view.values
                        if not base_type.get("counting"):
                            base_type["counting"] = {}
                        base_type["counting"]["enabled"] = True if enabled == "yes" else False
                        base_type["counting"]["offence_1"], base_type["counting"]["offence_2"], base_type["counting"]["offence_3"] = r1[0].id, r2[0].id, r3[0].id

                    case "delete":
                        guild_settings["infractions"]["infractions"].pop(index)
                        try:
                            await self.bot.settings.update(guild_settings)
                        except KeyError:
                            guild_settings["_id"] = ctx.guild.id
                            await self.bot.settings.update(guild_settings)
                        await message.edit(
                            content=f"{successEmoji} **{infraction_type_name}** has been successfully deleted!",
                            view=None,
                            embed=None,
                        )
                        break
                    case "finish":
                        guild_settings["infractions"]["infractions"][index] = base_type
                        try:
                            await self.bot.settings.update(guild_settings)
                        except KeyError: # If nothing changes this loves to error out. idk why but don't ask me, probably a pymongo thing
                            guild_settings["_id"] = ctx.guild.id
                            await self.bot.settings.update(guild_settings)
                            logging.warning("_id failure")
                        await message.edit(
                            content=None,
                            view=discord.ui.LayoutView().add_item(discord.ui.Container().add_item(discord.ui.TextDisplay(f"### Submitted\nThe infraction type **{infraction_type_name}** has been submitted."))),
                            embed=None,
                        )
                        break

async def setup(bot):
    await bot.add_cog(StaffConduct(bot))
