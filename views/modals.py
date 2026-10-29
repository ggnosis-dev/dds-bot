import discord

from helpers.messages import UtilityMsgs as Messages


class JoinRankingsModal(discord.ui.Modal):
	def __init__(
		self,
		server_name: str,
	):
		super().__init__(title="Opt-In to Server Rankings?", timeout=180)

		self.server_name = server_name
		self._build_modal()

	async def on_submit(self, interaction: discord.Interaction):
		self.name = self.name_entry.value.strip()
		await interaction.response.defer()
		self.stop()

	def _build_modal(self):
		name_entry = discord.ui.TextInput(
			style=discord.TextStyle.short,
			default=self.server_name,
			required=True,
			max_length=16,
		)

		checkbox = discord.ui.Checkbox(default=False)

		self.add_item(
			discord.ui.Label(text="Name/Nickname", component=name_entry, description=Messages.join_ranking_alphanumeric())
		)
		self.add_item(discord.ui.Label(text="Opt-In to Name Appearing in Server Rankings?", component=checkbox))
		self.add_item(discord.ui.TextDisplay(content=Messages.join_ranking_name_warning()))

		self.name_entry = name_entry
		self.checkbox = checkbox


# class UnusedShopModal(discord.ui.Modal):
# 	def __init__(
# 		self,
# 		entries: list[ShopItemData],
# 		title: str,
# 		*,
# 		timeout: int = 180,
# 		ephemeral_response: bool = True,
# 	):
# 		super().__init__(title=title, timeout=timeout)

# 		self.entries = sorted(entries, key=lambda i: i.item_id)
# 		self.ephemeral_response = ephemeral_response
# 		self._build_modal()

# 	async def on_submit(self, interaction: discord.Interaction):
# 		await interaction.response.send_message(f"Test {self.option.label}", ephemeral=self.ephemeral_response)

# 	def _build_modal(self):
# 		# Build an image with Emotes here.
# 		self.add_item(
# 			discord.ui.TextDisplay(
# 				content=f"{Emotes.GEM.value}{Emotes.GEM.value}{Emotes.GEM.value} How many would you like?"
# 			)
# 		)

# 		if len(self.entries) > 1:
# 			options = [
# 				discord.SelectOption(label=i.name, description=i.description, value=str(i.item_id)) for i in self.entries
# 			]
# 			select = discord.ui.Select(options=options)
# 			self.add_item(discord.ui.Label(text="Select The Item", component=select))

# 		option = discord.ui.TextInput(
# 			style=discord.TextStyle.short,
# 			default="1",
# 			required=True,
# 			max_length=2,
# 		)
# 		self.add_item(discord.ui.Label(text="Quantity", component=option))
# 		self.add_item(discord.ui.TextDisplay(content="-# That'll cost you ."))

# 		self.option = option
