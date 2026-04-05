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

    async def fetch_command_ids(self) -> dict[str, int]:
        if not hasattr(self, "_command_ids"):
            fetched = await self.context.bot.tree.fetch_commands()
            self._command_ids = {cmd.name: cmd.id for cmd in fetched}
        return self._command_ids
    
    async def get_command_mention(self, command: commands.Command) -> str:
        if not isinstance(command, (commands.HybridCommand, commands.HybridGroup)):
            return f"`{self.get_command_signature(command)}`"

        app_command = command.app_command
        qualified_name = app_command.qualified_name
        top_level_name = qualified_name.split()[0]

        command_ids = await self.fetch_command_ids()
        cmd_id = command_ids.get(top_level_name)
        if cmd_id:
            return f"</{qualified_name}:{cmd_id}>"

        return f"`{self.get_command_signature(command)}`"

    def get_command_description(self, command: commands.Command) -> str:
        return command.help or command.brief or command.description or "No description provided."

    async def format_commands(self, commands_list, indent=0):
        lines = []
        for c in sorted(commands_list, key=lambda c: c.name):
            prefix = "  " * indent
            description = self.get_command_description(c)
            description = f": {description.strip()}" if description else ""
            lines.append(f"{prefix}- {await self.get_command_mention(c)}{description}")
            if isinstance(c, commands.Group):
                lines.extend(await self.format_commands(c.commands, indent + 1))
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
                lines = await self.format_commands(filtered)
                page = self.make_page(
                    cog_name,
                    [
                        discord.ui.Container()
                        .add_item(discord.ui.TextDisplay(f"### {cog_name}\n"))
                        .add_item(discord.ui.Separator())
                        .add_item(discord.ui.TextDisplay("\n".join(lines)))
                        .add_item(discord.ui.TextDisplay("-# These commands should be clickable and will automatically show you the arguments. Ones that do not have these are not executable. Note that Vencord users may not be able to see them regardless."))
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

        lines = await self.format_commands(filtered)
        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay(f"### {cog.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay("\n".join(lines)))
        )
        await self._send(view=discord.ui.LayoutView().add_item(container))

    async def send_group_help(self, group: commands.Group) -> None:
        filtered = await self.filter_commands(group.commands, sort=True)
        mention = await self.get_command_mention(group)

        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay(f"### {group.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(
                f"{mention}\n"
                f"{self.get_command_description(group)}"
            ))
        )

        if filtered:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay("### Subcommands"))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay("\n".join(await self.format_commands(filtered))))

        await self._send(view=discord.ui.LayoutView().add_item(container))

    async def send_command_help(self, command: commands.Command) -> None:
        mention = await self.get_command_mention(command)

        container = (
            discord.ui.Container()
            .add_item(discord.ui.TextDisplay(f"### {command.qualified_name}"))
            .add_item(discord.ui.Separator())
            .add_item(discord.ui.TextDisplay(
                f"{mention}\n"
                f"{self.get_command_description(command)}"
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