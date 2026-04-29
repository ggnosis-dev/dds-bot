import asyncio
import discord
import typing


class ConfirmationView(discord.ui.LayoutView):
	def __init__(self, message: str, colour: int = 0xE93700, timeout: float = 60.0):
		super().__init__(timeout = timeout)
		self.message = message
		self.colour = colour
		self.confirmed: bool | None = None

		self._event = asyncio.Event()

		self._build_layout()


	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		action_row = ui.ActionRow(
			self.ConfirmButton('Confirm', discord.ButtonStyle.success)
		)

		container.add_item(ui.TextDisplay(self.message))
		container.add_item(action_row)

		self.add_item(container)

	
	async def wait_for_response(self) -> bool | None:
		await self._event.wait()
		return self.confirmed
	

	async def on_timeout(self) -> None:
		self.confirmed = None
		self._event.set()


	class ConfirmButton(discord.ui.Button):
		def __init__(self, label: str, style: discord.ButtonStyle) -> None:
			super().__init__(label = label, style = style, custom_id = "confirm")

		async def callback(self, interaction: discord.Interaction) -> None:
			view = typing.cast(ConfirmationView, self.view)
			view.confirmed = True
			view._event.set()
			await interaction.response.edit_message(
				content = "Confirmed", view = None
			)
