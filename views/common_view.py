import asyncio

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

import discord

from discord.ext import commands

from entities.view_data import DEFAULT_PAGE_SIZE
from shared_enums import EmbedColours


class MessageView(discord.ui.LayoutView):
	"""Standard message wrapped in a embed like view."""

	def __init__(
		self,
		message: str,
		*,
		thumbnail: str | None,
		colour: int,
	):
		super().__init__()
		self.message = message
		self.thumbnail = thumbnail
		self.colour = colour
		self._build_layout()

	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)

		if self.thumbnail is not None:
			section = ui.Section(accessory=ui.Thumbnail(media=self.thumbnail))
			section.add_item(ui.TextDisplay(self.message))
			container.add_item(section)
		else:
			container.add_item(ui.TextDisplay(self.message))

		self.add_item(container)

	@classmethod
	async def send(
		cls,
		destination: discord.abc.Messageable,
		message: str,
		thumbnail: str | None = None,
		colour: int = EmbedColours.DEFAULT.value,
	) -> discord.Message:
		view = cls(message, thumbnail=thumbnail, colour=colour)
		return await destination.send(view=view)


class ConfirmationView(discord.ui.LayoutView):
	def __init__(
		self,
		message: str,
		exclusive_to: int,
		*,
		confirm_label: str,
		deny_label: str,
		confirm_colour: discord.ButtonStyle,
		deny_colour: discord.ButtonStyle,
		thumbnail: str | None,
		colour: int,
		timeout: float,
	) -> None:
		super().__init__(timeout=timeout)

		self.message = message
		self.exclusive_to = exclusive_to
		self.confirm_label = confirm_label
		self.deny_label = deny_label
		self.confirm_colour = confirm_colour
		self.deny_colour = deny_colour
		self.thumbnail = thumbnail
		self.colour = colour
		self.timed_out: bool = False
		self.confirmed: bool | None = None
		self.msg: discord.Message | None = None

		self._event = asyncio.Event()

		self._build_layout()

	@classmethod
	async def send(
		cls,
		ctx: commands.Context | discord.Interaction,
		message: str,
		exclusive_to: int,
		confirm_label: str = "Confirm",
		deny_label: str = "Deny",
		confirm_colour: discord.ButtonStyle = discord.ButtonStyle.success,
		deny_colour: discord.ButtonStyle = discord.ButtonStyle.danger,
		thumbnail: str | None = None,
		colour: int = EmbedColours.DEFAULT.value,
		timeout: float = 20.0,
	) -> bool | None:
		"""Send the message and begin a wait for response timer."""
		view = cls(
			message,
			exclusive_to,
			confirm_label=confirm_label,
			deny_label=deny_label,
			confirm_colour=confirm_colour,
			deny_colour=deny_colour,
			thumbnail=thumbnail,
			colour=colour,
			timeout=timeout,
		)

		if isinstance(ctx, commands.Context):
			msg = await ctx.send(view=view)
		elif isinstance(ctx, discord.Interaction):
			await ctx.response.send_message(view=view)
			msg = await ctx.original_response()
		else:
			raise TypeError(f"ERROR: ctx was an unsupported type: {type(ctx)}")

		view.msg = msg
		return await view.wait_for_response()

	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)

		if self.thumbnail is not None:
			section = ui.Section(accessory=ui.Thumbnail(media=self.thumbnail))
			section.add_item(ui.TextDisplay(self.message))
			container.add_item(section)
		else:
			container.add_item(ui.TextDisplay(self.message))

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		action_row = ui.ActionRow(
			self.ConfirmButton(self.confirm_label, True, self.confirm_colour),
			self.ConfirmButton(self.deny_label, False, self.deny_colour),
		)

		container.add_item(action_row)

		if self.timed_out:
			container.add_item(ui.TextDisplay("-# Timed Out"))

		self.add_item(container)

	async def wait_for_response(self) -> bool | None:
		await self._event.wait()
		return self.confirmed

	async def on_timeout(self) -> None:
		self.confirmed = None
		self.timed_out = True
		self._event.set()

		self.clear_items()
		self._build_layout()
		self._disable_buttons()

		if self.msg:
			await self.msg.edit(view=self)

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

			if view.exclusive_to != interaction.user.id:
				return

			view.confirmed = self.value
			view._event.set()
			view.stop()
			view._disable_buttons()

			await interaction.response.edit_message(view=view)


EntryT = TypeVar("EntryT")


class BaseLayoutView(ABC, Generic[EntryT], discord.ui.LayoutView):
	"""Our own quirky little base class for displaying things in a layout view."""

	def __init__(
		self,
		entries: list[EntryT],
		page: int = 1,
		page_size: int = DEFAULT_PAGE_SIZE,
		colour: int = EmbedColours.DEFAULT.value,
	) -> None:
		"""
		Init for the base table view.

		Args:
			entries (list[EntryT]): List of a generic Entry Type.
			page (int): Current page number of the view. Defaults to 1.
			page_size (int): The number of entries to show on the page. Defaults to 10.
			colour (int): Colour of the view's left side.
		"""

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
		"""
		Get the entries that will populate the page, acknowledging any filters that come from overriding
		_get_filtered_entries.
		"""
		entries = self._get_filtered_entries()

		self.total_pages = int(max(1, (len(entries) + self.page_size - 1) / self.page_size))
		self.page = max(1, min(self.page, self.total_pages))

		start_index = (self.page - 1) * self.page_size
		end_index = start_index + self.page_size

		# Use delimiter to slice out entries.
		return entries[start_index:end_index]

	def _get_filtered_entries(self) -> list[EntryT]:
		"""Override for dedicated filters, such as Compendium's race filter."""
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
