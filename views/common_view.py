import asyncio
import typing

import discord

from discord.ext import commands


class MessageView(discord.ui.LayoutView):
	def __init__(
		self,
		message: str,
		image: str | None = None,
		colour: int = 0xE93700,
	):
		super().__init__()
		self.message = message
		self.image = image
		self.colour = colour
		self._build_layout()

	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)

		if self.image is not None:
			section = ui.Section(accessory=ui.Thumbnail(media=self.image))
			section.add_item(ui.TextDisplay(self.message))
			container.add_item(section)
		else:
			container.add_item(ui.TextDisplay(self.message))

		self.add_item(container)


class ConfirmationView(discord.ui.LayoutView):
	def __init__(
		self,
		message: str,
		confirmLabel: str = "Confirm",
		denyLabel: str = "Deny",
		confirmColour: discord.ButtonStyle = discord.ButtonStyle.success,
		denyColour: discord.ButtonStyle = discord.ButtonStyle.danger,
		image: str | None = None,
		colour: int = 0xE93700,
		timeout: float = 10.0,
	):
		super().__init__(timeout=timeout)

		self.message = message
		self.confirmLabel = confirmLabel
		self.denyLabel = denyLabel
		self.confirmColour = confirmColour
		self.denyColour = denyColour
		self.image = image
		self.colour = colour
		self.timedOut: bool = False
		self.confirmed: bool | None = None
		self.msg = None

		self._event = asyncio.Event()

		self._build_layout()

	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)

		if self.image is not None:
			section = ui.Section(accessory=ui.Thumbnail(media=self.image))
			section.add_item(ui.TextDisplay(self.message))
			container.add_item(section)
		else:
			container.add_item(ui.TextDisplay(self.message))

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		action_row = ui.ActionRow(
			self.ConfirmButton(self.confirmLabel, True, self.confirmColour),
			self.ConfirmButton(self.denyLabel, False, self.denyColour),
		)

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
			await self.msg.edit(view=self)

	async def send_message(self, ctx: commands.Context | discord.Interaction) -> bool | None:
		if type(ctx) is commands.Context:
			msg = await ctx.send(view=self)
		elif type(ctx) is discord.Interaction:
			await ctx.response.send_message(view=self)
			msg = await ctx.original_response()
		else:
			raise TypeError(f"ERROR: ctx was an unsupported type: {type(ctx)}")

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
		def __init__(self, label: str, value: bool, style: discord.ButtonStyle) -> None:
			super().__init__(label=label, style=style)
			self.value = value

		async def callback(self, interaction: discord.Interaction) -> None:
			view = typing.cast(ConfirmationView, self.view)
			view.confirmed = self.value
			view._event.set()
			view.stop()
			view._disable_buttons()

			await interaction.response.edit_message(view=view)
