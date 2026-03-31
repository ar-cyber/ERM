import discord
from utils.constants import BLANK_COLOR
from custommodal import CustomModal


class CounterButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="0", style=discord.ButtonStyle.primary, row=row)
        self.voters = set()

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if user.id in self.voters:
            self.voters.remove(user.id)
            self.label = str(int(self.label) - 1)
            await interaction.response.send_message(
                f"Your vote has been removed.", ephemeral=True
            )
        else:
            self.voters.add(user.id)
            self.label = str(int(self.label) + 1)
            await interaction.response.send_message(
                f"Your vote has been added.", ephemeral=True
            )
        await interaction.message.edit(view=self.view)


class ViewVotersButton(discord.ui.Button):
    def __init__(self, row, counter_button):
        super().__init__(
            label="🔍View Voters", style=discord.ButtonStyle.secondary, row=row
        )
        self.counter_button = counter_button

    async def callback(self, interaction: discord.Interaction):
        voters = [
            interaction.guild.get_member(user_id).mention
            for user_id in self.counter_button.voters
        ]
        voter_list = "\n".join(voters) if voters else "No votes yet."
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Voters", description=voter_list, color=BLANK_COLOR
            ),
            ephemeral=True,
        )

class ButtonCustomisation(discord.ui.View):
    def __init__(self, command_data: dict, user_id: int):
        super().__init__(timeout=600)
        for item in command_data.get("buttons") or []:
            self.add_item(
                discord.ui.Button(
                    label=item["label"],
                    url=item["url"],
                    row=item["row"],
                    style=discord.ButtonStyle.url,
                )
            )

        self.command_data = command_data
        self.sustained_interaction = None
        self.value = None
        self.user_id = user_id

    @discord.ui.button(label="Add Button", row=4)
    async def add_button(self, interaction: discord.Interaction, _):
        if len(self.children) >= 25:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Limitation",
                    description="You can only have a maximum of 25 buttons per custom command.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        modal = CustomModal(
            "Add a Button",
            [
                (
                    "label",
                    discord.ui.TextInput(
                        label="Label",
                        max_length=80,
                        placeholder="Label of the button",
                        required=True,
                    ),
                ),
                (
                    "url",
                    discord.ui.TextInput(
                        label="URL",
                        max_length=500,
                        placeholder="URL of the button",
                        required=True,
                    ),
                ),
                (
                    "row",
                    discord.ui.TextInput(
                        label="Row", placeholder="Row of the button (e.g. 0, 1, 2, 3)"
                    ),
                ),
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(modal)
        await modal.wait()
        # Input validations
        if not all([i.isdigit() for i in modal.row.value.strip()]):
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Row",
                    description="The row you provided is not a valid number.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if int(modal.row.value.strip()) > 4:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Row",
                    description="The row you provided must be within the range 0-4.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if int(modal.row.value.strip()) < 0:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Row",
                    description="The row you provided must be within the range 0-4.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if not modal.label.value.strip():
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Label",
                    description="The label you provided is not valid.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if not modal.url.value.strip():
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid URL",
                    description="The URL you provided is not valid.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        if not any(
            [
                modal.url.value.strip().startswith(prefix)
                for prefix in ["https://", "http://"]
            ]
        ):
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid URL",
                    description="The URL you provided is not valid.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        message = interaction.message
        if self.sustained_interaction:
            message = await self.sustained_interaction.original_response()

        relevant_item = discord.ui.Button(
            label=modal.label.value.strip(),
            url=modal.url.value.strip(),
            row=int(modal.row.value.strip()),
            style=discord.ButtonStyle.url,
        )
        self.add_item(relevant_item)

        try:
            await message.edit(view=self)
        except discord.HTTPException:
            self.remove_item(relevant_item)
            return

        if self.command_data.get("buttons") is not None:
            self.command_data["buttons"].append(
                {
                    "label": modal.label.value.strip(),
                    "url": modal.url.value.strip(),
                    "row": int(modal.row.value.strip()),
                }
            )
        else:
            self.command_data["buttons"] = [
                {
                    "label": modal.label.value.strip(),
                    "url": modal.url.value.strip(),
                    "row": int(modal.row.value.strip()),
                }
            ]

    @discord.ui.button(label="Remove Button", row=4)
    async def remove_button(self, interaction: discord.Interaction, _):
        modal = CustomModal(
            "Remove a Button",
            [
                (
                    "label",
                    discord.ui.TextInput(
                        label="Label",
                        max_length=80,
                        placeholder="Label of the button",
                        required=True,
                    ),
                ),
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(modal)
        await modal.wait()
        # Input validations

        message = interaction.message
        if self.sustained_interaction:
            message = await self.sustained_interaction.original_response()

        for item in self.command_data.get("buttons") or []:
            if item["label"].lower() == modal.label.value.strip().lower():
                self.command_data["buttons"].remove(item)

        for button in self.children:
            if isinstance(button, discord.ui.Button):
                if button.label.lower() == modal.label.value.strip().lower():
                    if button.label not in [
                        "Add Button",
                        "Remove Button",
                        "Counter Button",
                        "Cancel",
                        "Finish",
                    ]:
                        self.remove_item(button)
                        break

        await message.edit(view=self)

    @discord.ui.button(label="Counter Button", row=4)
    async def add_counter(self, interaction: discord.Interaction, _):
        if len(self.children) >= 25:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Limitation",
                    description="You can only have a maximum of 25 buttons per custom command.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        modal = CustomModal(
            "Add a Button",
            [
                (
                    "row",
                    discord.ui.TextInput(
                        label="Row", placeholder="Row of the button (e.g. 0, 1, 2, 3)"
                    ),
                )
            ],
            {"ephemeral": True},
        )
        await interaction.response.send_modal(modal)
        await modal.wait()

        if not modal.children[0].value.isdigit():
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Row",
                    description="The row you provided is not a valid number.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        row = int(modal.children[0].value.strip())

        if row > 4 or row < 0:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Row",
                    description="The row you provided must be within the range 0-4.",
                    color=BLANK_COLOR,
                ),
                ephemeral=True,
            )

        counter_button = CounterButton(row=row)
        view_voters_button = ViewVotersButton(row=row, counter_button=counter_button)

        self.add_item(counter_button)
        self.add_item(view_voters_button)

        message = interaction.message
        if self.sustained_interaction:
            message = await self.sustained_interaction.original_response()

        try:
            await message.edit(view=self)
        except discord.HTTPException:
            self.remove_item(counter_button)
            self.remove_item(view_voters_button)
            return

        if self.command_data.get("buttons") is not None:
            self.command_data["buttons"].append({"label": "0", "row": row})
        else:
            self.command_data["buttons"] = [{"label": "0", "row": row}]

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        self.value = False
        pass

    @discord.ui.button(
        label="Finish", style=discord.ButtonStyle.green, row=4, disabled=False
    )
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        self.value = True
        self.stop()
