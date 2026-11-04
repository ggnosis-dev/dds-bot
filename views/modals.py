import discord

from helpers.messages import UtilityMsgs as Messages


class NotificationsModal(discord.ui.Modal):
	def __init__(
		self,
		settings: dict[str, bool],
	):
		super().__init__(title="Notification Settings", timeout=180)

		self.settings = settings
		self._build_modal()

	async def on_submit(self, interaction: discord.Interaction):
		await interaction.response.defer()
		self.stop()

	def _build_modal(self):
		checkboxes = []

		for key, value in self.settings.items():
			cb = discord.ui.Checkbox(default=value)
			self.add_item(discord.ui.Label(text=Messages.get_notification_label(key), component=cb))
			checkboxes.append(cb)

		self.checkboxes = checkboxes
