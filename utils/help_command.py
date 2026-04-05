from typing import Any, Callable, List, Mapping
from utils.paginators_new import CustomPage, SelectPagination
import discord
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    @property
    def clean_prefix(self) -> str:
        if self.context.interaction is not None:
            return "/"
        return self.context.clean_prefix

    def get_command_signature(self, command: commands.Command) -> str:
        return f"{self.clean_prefix}{command.qualified_name} {command.signature}".strip()

    def _make_help_button(self) -> discord.ui.ActionRow:
        button = discord.ui.Button(label="Get Help Reading This")

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
            description = c.help or c.brief or c.description
            description = f" — {description.strip()}" if description else ""
            lines.append(f"{prefix}- `{self.get_command_signature(c)}`{description}")
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

    async def _send(self, **kwargs):
        ctx = self.context
        if ctx.interaction is not None:
            await ctx.interaction.followup.send(**kwargs)
        else:
            await ctx.reply(**kwargs)

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, List[commands.Command[Any, Callable[..., Any], Any]]],
    ) -> None:
        pages = []
        for cog, commands_list in mapping.items():
            all_commands = list(commands_list)
            for cmd in self.context.bot.commands:
                if cmd not in all_commands and getattr(cmd.cog, "qualified_name", None) == getattr(cog, "qualified_name", None):
                    all_commands.append(cmd)

            filtered = await self.filter_commands(all_commands, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "No Category")
                lines = self.format_commands(filtered)
                page = self.make_page(
                    cog_name,
                    [
                        discord.ui.Container()
                        .add_item(discord.ui.TextDisplay(f"### {cog_name}\n"))
                        .add_item(discord.ui.Separator())
                        .add_item(discord.ui.TextDisplay("\n".join(lines)))
                        .add_item(discord.ui.Separator())
                        .add_item(self._make_help_button())
                    ],
                )
                pages.append(page)

        if not pages:
            await self._send(content="No commands available.")
            return

        paginator = self._send_paginator(pages)
        await self._send(view=paginator.get_current_view())

    async def send_cog_help(self, cog: commands.Cog) -> None:
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            await self._send(content="No commands available in this category.")
            return

        lines = self.format_commands(filtered)
        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay(f"### {cog.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay("\n".join(lines)))
            .add_item(discord.ui.Separator())
            .add_item(self._make_help_button())
        )
        await self._send(view=discord.ui.LayoutView().add_item(container))

    async def send_group_help(self, group: commands.Group) -> None:
        filtered = await self.filter_commands(group.commands, sort=True)

        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay(f"### {group.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(
                f"`{self.get_command_signature(group)}`\n"
                f"{group.help or 'No description provided.'}"
            ))
        )

        if filtered:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay("### Subcommands"))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay("\n".join(self.format_commands(filtered))))

        await self._send(view=discord.ui.LayoutView().add_item(container))

    async def send_command_help(self, command: commands.Command) -> None:
        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay(f"### {command.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(
                f"`{self.get_command_signature(command)}`\n"
                f"{command.help or 'No description provided.'}"
            ))
        )

        if command.aliases:
            alias_tags = "\n".join(f"> `{a}`" for a in command.aliases)
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay("### Aliases"))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(alias_tags))

        await self._send(view=discord.ui.LayoutView().add_item(container))

    async def send_error_message(self, error: str) -> None:
        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay("### Error"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(error))
        )
        await self._send(view=discord.ui.LayoutView().add_item(container))