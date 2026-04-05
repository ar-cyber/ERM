from typing import Any, Callable, List, Mapping
from utils.paginators_new import CustomPage, SelectPagination
import discord
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    def _make_help_button(self) -> discord.ui.ActionRow:
        button = discord.ui.Button(label="Get Help Reading This", emoji="❔")

        async def callback(interaction: discord.Interaction):
            cont = discord.ui.Container().add_item(
                discord.ui.TextDisplay(
                    "### How do I read this?\n"
                    "Each component of a help command line has a use. They represent different properties of a command, such as their arguments.\n\n"
                    "**General Scaffold**\n"
                    "All help commands are formatted like this: \n"
                    "`prefix[command name] [subcommand if applicable] <required arguments ...=default> [optional arguments]`.\n"
                    "All of these can be replaced with actual properties, such as: \n`>duty admin Android365436 default`\n\n"
                    "**But what about `[a|b|c|d]`?**\n"
                    "These are **command aliases**, which are shortened versions of a command name. \n"
                    "For example, the lengthy command name `>search` can be run as `>s` instead.\n\n"
                    "**How do the dot points work?**\n"
                    "The outer dot-points are the **base command**, which is normally the command name.\nThe inner dot points are the **subcommand**, which is a command that belongs to that base command.\nFor example, `>erlc info` is a subcommand of `>erlc`, however, not all base commands can be run."

                )
            )
            await interaction.response.send_message(
                view=discord.ui.LayoutView().add_item(cont), ephemeral=True
            )

        button.callback = callback
        return discord.ui.ActionRow(button)
    def format_commands(self, commands_list, indent=0):
        lines = []
        for c in sorted(commands_list, key=lambda c: c.name):
            prefix = "  " * indent
            lines.append(f"{prefix}- `{self.get_command_signature(c)}`")
            if isinstance(c, commands.Group):
                lines.extend(self.format_commands(c.commands, indent + 1))
        return lines

    def make_page(self, identifier: str, containers: list[discord.ui.Container]) -> CustomPage:
        page = CustomPage()
        page.containers = containers
        page.identifier = identifier
        return page

    def _send_paginator(self, pages: list[CustomPage]):
        return SelectPagination(
            self.context.bot,
            self.context.author.id,
            pages,
        )

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, List[commands.Command[Any, Callable[..., Any], Any]]],
    ) -> None:
        pages = []
        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "No Category")
                lines = self.format_commands(filtered)
                page = self.make_page(
                    cog_name,
                    [
                        discord.ui.Container(accent_colour=discord.Colour.blurple())
                        
                        .add_item(discord.ui.TextDisplay(f"### {cog_name}\n"))
                        .add_item(discord.ui.Separator())
                        .add_item(discord.ui.TextDisplay("\n".join(lines)))
                        .add_item(discord.ui.Separator())
                        .add_item(self._make_help_button())
                    ],
                )
                pages.append(page)

        if not pages:
            await self.get_destination().send("No commands available.")
            return

        paginator = self._send_paginator(pages)
        await self.get_destination().send(view=paginator.get_current_view())

    async def send_cog_help(self, cog: commands.Cog) -> None:
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            await self.get_destination().send("No commands available in this category.")
            return

        lines = self.format_commands(filtered)
        page = self.make_page(
            cog.qualified_name,
            [
                discord.ui.Container(accent_colour=discord.Colour.blurple())
                .add_item(discord.ui.TextDisplay(f"### {cog.qualified_name}"))
                .add_item(discord.ui.Separator())
                .add_item(discord.ui.TextDisplay("\n".join(lines)))
            ],
        )
        paginator = self._send_paginator([page])
        await self.get_destination().send(view=paginator.get_current_view())

    async def send_group_help(self, group: commands.Group) -> None:
        filtered = await self.filter_commands(group.commands, sort=True)

        containers = [
            discord.ui.Container(accent_colour=discord.Colour.blurple())
            .add_item(discord.ui.TextDisplay(f"### {group.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(
                f"`{self.get_command_signature(group)}`\n"
                f"{group.help or 'No description provided.'}"
            ))
        ]

        if filtered:
            containers.append(
                discord.ui.Container(accent_colour=discord.Colour.blurple())
                .add_item(discord.ui.TextDisplay("### Subcommands"))
                .add_item(discord.ui.Separator())
                .add_item(discord.ui.TextDisplay("\n".join(self.format_commands(filtered))))
            )

        paginator = self._send_paginator([self.make_page(group.qualified_name, containers)])
        await self.get_destination().send(view=paginator.get_current_view())

    async def send_command_help(self, command: commands.Command) -> None:
        containers = [
            discord.ui.Container(accent_colour=discord.Colour.blurple())
            .add_item(discord.ui.TextDisplay(f"### {command.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(
                f"`{self.get_command_signature(command)}`\n"
                f"{command.help or 'No description provided.'}"
            ))
        ]

        if command.aliases:
            alias_tags = "\n".join(f"> `{a}`" for a in command.aliases)
            containers.append(
                discord.ui.Container(accent_colour=discord.Colour.blurple())
                .add_item(discord.ui.TextDisplay("### Aliases"))
                .add_item(discord.ui.Separator())
                .add_item(discord.ui.TextDisplay(alias_tags))
            )

        paginator = self._send_paginator([self.make_page(command.qualified_name, containers)])
        await self.get_destination().send(view=paginator.get_current_view())

    async def send_error_message(self, error: str) -> None:
        container = (
            discord.ui.Container(accent_colour=discord.Colour.red())
            .add_item(discord.ui.TextDisplay("### Error"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(error))
        )
        await self.get_destination().send(
            view=discord.ui.LayoutView().add_item(container)
        )