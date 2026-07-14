import asyncio

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

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
			view = cast(ConfirmationView, self.view)
			view.confirmed = self.value
			view._event.set()
			view.stop()
			view._disable_buttons()

			await interaction.response.edit_message(view=view)


DEFAULT_PAGE_SIZE = 10
DEFAULT_COLOUR = 0x1E452F
EntryT = TypeVar("EntryT")


class BaseLayoutView(ABC, Generic[EntryT], discord.ui.LayoutView):
	def __init__(
		self,
		entries: list[EntryT],
		page: int = 1,
		page_size: int = DEFAULT_PAGE_SIZE,
		colour: int = DEFAULT_COLOUR,
	) -> None:
		# Run the standard layout view stuff.
		super().__init__()

		self.entries = entries
		self.page = page
		self.page_size = page_size
		self.total_pages = 1
		self.colour = colour
		self.show_info: bool = False

	class PageButton(discord.ui.Button):
		"""Custom button for navigating between pages."""

		def __init__(self, direction: str) -> None:
			if direction == "prev":
				super().__init__(label="<", style=discord.ButtonStyle.primary)
			else:
				super().__init__(label=">", style=discord.ButtonStyle.primary)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a page navigation button is clicked. Allows wrapping around the pages."""

			view = cast(BaseLayoutView, self.view)

			if self.label == "<":
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == ">":
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			view.refresh()
			await interaction.response.edit_message(view=view)

	class InfoButton(discord.ui.Button):
		"""Custom button for showing more information in a view."""

		def __init__(self, show_info: bool) -> None:
			super().__init__(
				label="ⓘ ◥" if show_info else "ⓘ ◢",
				style=discord.ButtonStyle.secondary,
			)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when the information button is clicked. Allows wrapping around the pages."""

			view = cast(BaseLayoutView, self.view)
			view.show_info = not view.show_info

			view.refresh()
			await interaction.response.edit_message(view=view)

	def refresh(self) -> None:
		self.clear_items()
		self._build_layout()

	def _get_page_entries(self) -> list[EntryT]:
		self.total_pages = int(max(1, (len(self.entries) + self.page_size - 1) / self.page_size))
		self.page = max(1, min(self.page, self.total_pages))

		start_index = (self.page - 1) * self.page_size
		end_index = start_index + self.page_size

		# Use delimiter to slice out entries.
		return self.entries[start_index:end_index]

	def _get_filtered_entries(self) -> list[EntryT]:
		return self.entries

	@abstractmethod
	def _build_layout(self) -> None:
		pass

	@abstractmethod
	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		pass

	def _build_footer(self, container: discord.ui.Container) -> discord.ui.Container:
		"""Footer shows number of pages and given there's more than one page, will create page navigation."""
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(discord.ui.TextDisplay(f"-# Page {self.page} of {self.total_pages}"))

		if self.total_pages != 1:
			page_nav = discord.ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))
			container.add_item(page_nav)

		return container
