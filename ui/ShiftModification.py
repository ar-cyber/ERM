import discord
from utils.utils import generalised_interaction_check_failure

class ShiftModificationDropdown(discord.ui.Select):
    def __init__(self, user_id, other=False):
        self.user_id = user_id
        if other is False:
            options = [
                discord.SelectOption(
                    label="On Duty",
                    value="on",
                    description="Start your in-game shift",
                ),
                discord.SelectOption(
                    label="Toggle Break",
                    value="break",
                    description="Taking a break? Toggle your break status",
                ),
                discord.SelectOption(
                    label="Off Duty",
                    value="off",
                    description="End your in-game shift",
                ),
                discord.SelectOption(
                    label="Void shift",
                    value="void",
                    description="Void your in-game shift. This is irreversible.",
                ),
            ]
        else:
            options = [
                discord.SelectOption(
                    label="On Duty",
                    value="on",
                    description="Start their in-game shift",
                ),
                discord.SelectOption(
                    label="Toggle Break",
                    value="break",
                    description="Taking a break? Toggle their break status",
                ),
                discord.SelectOption(
                    label="Off Duty",
                    value="off",
                    description="End their in-game shift",
                ),
            ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select an option", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.value = self.values[0]
            self.disabled = True
            for option in self.options:
                if option.value == self.values[0]:
                    option.default = True

            await interaction.message.edit(view=self.view)
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)

class ModificationSelectMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.00)
        self.value = None
        self.user_id = user_id

        self.add_item(ShiftModificationDropdown(self.user_id))



class AdministrativeActionsDropdown(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label="Add time",
                value="add",
                description="Add time to their current shift",
            ),
            discord.SelectOption(
                label="Remove time",
                value="remove",
                description="Remove time from their current shift",
            ),
            discord.SelectOption(
                label="Void shift",
                value="void",
                description="Void their shift, and remove it from the leaderboard",
            ),
            discord.SelectOption(
                label="Clear Member Shifts",
                value="clear",
                description="Clear all of their shifts from the leaderboard",
            ),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Administrative Actions",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            await interaction.response.defer()
            self.view.admin_value = self.values[0]
            self.disabled = True
            for option in self.options:
                if option.value == self.values[0]:
                    option.default = True

            for item in self.view.children:
                if isinstance(item, discord.ui.Select):
                    if item is not self:
                        item.disabled = True

            await interaction.message.edit(view=self.view)
            self.view.stop()
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await generalised_interaction_check_failure(interaction.followup)




class AdministrativeSelectMenu(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600.00)
        self.value = None
        self.admin_value = None
        self.user_id = user_id

        self.add_item(ShiftModificationDropdown(self.user_id, other=True))
        self.add_item(AdministrativeActionsDropdown(self.user_id))