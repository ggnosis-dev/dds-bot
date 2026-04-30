import asyncio
import discord
import typing


class ConfirmationView(discord.ui.LayoutView):
	def __init__(self, 
		message: str,
		confirmLabel: str = 'Confirm',
		denyLabel: str = 'Deny',
		colour: int = 0xE93700, 
		timeout: float = 10.0
	):
		super().__init__(timeout = timeout)
		self.message = message
		self.confirmLabel = confirmLabel
		self.denyLabel = denyLabel
		self.colour = colour
		self.timedOut: bool = False
		self.confirmed: bool | None = None
		self.msg: discord.Message | None = None
		
		self._event = asyncio.Event()

		self._build_layout()


	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		action_row = ui.ActionRow(
			self.ConfirmButton(self.confirmLabel, True, discord.ButtonStyle.success),
			self.ConfirmButton(self.denyLabel, False, discord.ButtonStyle.danger),
		)

		container.add_item(ui.TextDisplay(self.message))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(action_row)

		if self.timedOut:
			container.add_item(ui.TextDisplay("-# Timed Out"))

		self.add_item(container)

	
	async def wait_for_response(self) -> bool | None:
		await self._event.wait()
		return self.confirmed
	

	async def on_timeout(self) -> None:
		self.confirmed = None
		self.timedOut = True
		self._event.set()

		self.clear_items()
		self._build_layout()
		self._disable_buttons()

		if self.msg:
			await self.msg.edit(view = self)


	async def send_message(self, ctx) -> bool | None:
		msg = await ctx.send(view = self)
		self.msg = msg

		return await self.wait_for_response()


	def _disable_buttons(self) -> None:
		container = self.children[0]

		if isinstance(container, discord.ui.Container):
			for item in container.children:
				if isinstance(item, discord.ui.ActionRow):
					for button in item.children:
						if isinstance(button, discord.ui.Button):
							button.disabled = True


	class ConfirmButton(discord.ui.Button):
		def __init__(
			self, 
			label: str, 
			value: bool,
			style: discord.ButtonStyle
		) -> None:
			super().__init__(label = label, style = style)
			self.value = value

		async def callback(self, interaction: discord.Interaction) -> None:
			view = typing.cast(ConfirmationView, self.view)
			view.confirmed = self.value
			view._event.set()
			view.stop()
			view._disable_buttons()

			await interaction.response.edit_message(view = view)
