import discord
from utils.utils import generalised_interaction_check_failure
class SettingsSelectMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.0)
        self.value = None
        self.user_id = user_id

        self.add_item(SettingsDropdown(self.user_id))

class SettingsDropdown(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label="Staff Management",
                value="staff_management",
                description="Inactivity Notices, and managing staff members",
            ),
            discord.SelectOption(
                label="Anti-ping",
                value="antiping",
                description="Responding to certain pings, ping immunity",
            ),
            discord.SelectOption(
                label="Punishments",
                value="punishments",
                description="Punishing community members for rule infractions",
            ),
            discord.SelectOption(
                label="Moderation Sync",
                value="moderation_sync",
                description="Syncing moderation actions from Roblox to Discord",
            ),
            discord.SelectOption(
                label="Shift Management",
                value="shift_management",
                description="Shifts (duty on, duty off), and where logs should go",
            ),
            discord.SelectOption(
                label="Shift Types",
                value="shift_types",
                description="View and customise shift types",
            ),
            discord.SelectOption(
                label="Verification",
                value="verification",
                description="Roblox Verification, simplified!",
            ),
            discord.SelectOption(
                label="Game Logging",
                value="game_logging",
                description="Game Logging! Messages, STS, Events, and more!",
            ),
            discord.SelectOption(
                label="Customisation",
                value="customisation",
                description="Colours, branding, prefix, to customise to your liking",
            ),
            discord.SelectOption(
                label="Game Security",
                value="security",
                description="Anti-abuse detection, and security measures",
            ),
            discord.SelectOption(
                label="Privacy",
                value="privacy",
                description="Disable global warnings, privacy features",
            ),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select a category", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.value = self.values[0]
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)