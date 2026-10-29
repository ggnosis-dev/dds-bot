import asyncio

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

import discord

from shared_enums import EmbedColours

EntryT = TypeVar("EntryT")


class MessageView(discord.ui.LayoutView):
	"""Standard message wrapped in a embed like view."""

	def __init__(
		self,
		message: str,
		*,
		thumbnail: str | None = None,
		colour: int = EmbedColours.DEFAULT.value,
	):
		super().__init__()
		self.message = message
		self.thumbnail = thumbnail
		self.colour = colour
		self._build_layout()

	@classmethod
	async def send(cls, destination: discord.abc.Messageable, *args, **kwargs) -> discord.Message:
		"""
		Send a message wrapped in an emebd type view.

		Args:
			destination: Where to send message to.
			*args: Required arguments (see init).
			**kwargs: Keyword/optional arguments (see init).
		"""
		view = cls(*args, **kwargs)
		return await destination.send(view=view)

	@classmethod
	async def reply(cls, interaction: discord.Interaction, *args, ephemeral: bool = False, **kwargs):
		"""
		Send a message response wrapped in an emebd type view.

		Args:
			interaction (discord.Interaction): Initial interaction this will respond to.
			*args: Required arguments (see init).
			ephemeral (bool): Hides the view from other users.
			**kwargs: Keyword/optional arguments (see init).
		"""
		view = cls(*args, **kwargs)

		if interaction.response.is_done():
			await interaction.followup.send(view=view, ephemeral=True)
		else:
			await interaction.response.send_message(view=view, ephemeral=ephemeral)

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


class ResponseView(discord.ui.LayoutView):
	"""For views that require a response."""

	def __init__(self, exclusive_to: int, *, timeout: float = 20.0) -> None:
		super().__init__(timeout=timeout)
		self.exclusive_to = exclusive_to
		self.timed_out: bool = False
		self.confirmed: bool | None = None
		self.msg: discord.Message | None = None
		self.response_interaction: discord.Interaction | None = None
		self._event = asyncio.Event()

		# Subclasses call self._build_layout() once setup.

	def _build_layout(self) -> None:
		raise NotImplementedError

	@classmethod
	async def send(cls, destination: discord.abc.Messageable, *args, **kwargs) -> bool | None:
		"""
		Send a response message and begin a wait for response timer.

		Args:
			destination: Where to send message to.
			*args: Required arguments (see init).
			**kwargs: Keyword/optional arguments (see init).
		"""
		view = cls(*args, **kwargs)
		view.msg = await destination.send(view=view)
		return await view.wait_for_response()

	@classmethod
	async def send_view(cls, destination: discord.abc.Messageable, *args, **kwargs) -> ResponseView:
		"""
		Send view without starting the wait. Command returns the view so it can read the interaction afterwards,
		thus allowing followups like Modals.
		"""
		view = cls(*args, **kwargs)
		view.msg = await destination.send(view=view)
		return view

	@classmethod
	async def reply(cls, interaction: discord.Interaction, *args, ephemeral: bool = False, **kwargs) -> bool | None:
		"""
		Send a response message as an interaction response and begin a wait for response timer.

		Args:
			interaction (discord.Interaction): Initial interaction this will respond to.
			*args: Required arguments (see init).
			ephemeral (bool): Hides the view from other users.
			**kwargs: Keyword/optional arguments (see init).
		"""
		view = cls(*args, **kwargs)

		if interaction.response.is_done():
			view.msg = await interaction.followup.send(view=view, ephemeral=True, wait=True)
		else:
			await interaction.response.send_message(view=view, ephemeral=ephemeral)
			view.msg = await interaction.original_response()

		return await view.wait_for_response()

	async def wait_for_response(self) -> bool | None:
		"""Begin waiting on the event. Returns True/False after response triggers it to continue."""
		await self._event.wait()
		return self.confirmed

	async def on_timeout(self) -> None:
		"""Clean up the view on timeout."""
		self.confirmed = None
		self.timed_out = True
		self._event.set()
		self.clear_items()
		self._build_layout()
		self._disable_buttons()

	def on_finish(self, confirmed: bool = True, interaction: discord.Interaction | None = None) -> None:
		"""Clean up view, set self.confirmed."""
		self.confirmed = confirmed
		self.response_interaction = interaction
		self._event.set()
		self.stop()  # Stop listening to future interactions.
		self._disable_buttons()

	def interaction_excl_check(self, interaction: discord.Interaction) -> bool:
		"""True if user from the interaction is allowed."""
		return self.exclusive_to is None or interaction.user.id == self.exclusive_to

	def _disable_buttons(self) -> None:
		"""Get all children of container and disable the buttons. Must come after the layout is built."""
		container = self.children[0]

		if isinstance(container, discord.ui.Container):
			for item in container.children:
				if isinstance(item, discord.ui.ActionRow):
					for button in item.children:
						if isinstance(button, discord.ui.Button):
							button.disabled = True


class ConfirmationView(ResponseView):
	def __init__(
		self,
		message: str,
		exclusive_to: int,
		*,
		return_interaction: bool = False,
		trigger_id: str | None = None,
		confirm_label: str = "Confirm",
		deny_label: str | None = "Deny",
		confirm_colour: discord.ButtonStyle = discord.ButtonStyle.success,
		deny_colour: discord.ButtonStyle = discord.ButtonStyle.danger,
		thumbnail: str | None = None,
		colour: int = EmbedColours.DEFAULT.value,
		timeout: float = 20.0,
	) -> None:
		super().__init__(exclusive_to=exclusive_to, timeout=timeout)

		self.message = message
		self.return_interaction = return_interaction
		self.trigger_id = trigger_id  # Used for tutorials and eventually challenges.
		self.confirm_label = confirm_label
		self.deny_label = deny_label
		self.confirm_colour = confirm_colour
		self.deny_colour = deny_colour
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

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		buttons = [self.ConfirmButton(self.confirm_label, True, self.confirm_colour)]
		if self.deny_label is not None:
			buttons.append(self.ConfirmButton(self.deny_label, False, self.deny_colour))
		action_row = ui.ActionRow(*buttons)

		container.add_item(action_row)

		if self.timed_out:
			container.add_item(ui.TextDisplay("-# Timed Out"))

		self.add_item(container)

	class ConfirmButton(discord.ui.Button):
		def __init__(self, label: str, value: bool, style: discord.ButtonStyle) -> None:
			super().__init__(label=label, style=style)
			self.value = value

		async def callback(self, interaction: discord.Interaction) -> None:
			view = cast(ConfirmationView, self.view)

			# Check if user is allowed to interact with this.
			if not view.interaction_excl_check(interaction):
				return

			if view.return_interaction and self.value:
				view.on_finish(self.value, interaction)
			else:
				view.on_finish(self.value)
				await interaction.response.edit_message(view=view)

			if view.trigger_id is not None:
				# Calls on_tutorial_trigger (discord.py prefixes the on_).
				interaction.client.dispatch("tutorial_trigger", interaction, view.trigger_id)


class BaseLayoutView(ABC, Generic[EntryT], discord.ui.LayoutView):
	"""Our own quirky little base class for displaying things in a layout view."""

	def __init__(
		self,
		entries: list[EntryT],
		*,
		page_size: int,
		page: int = 1,
		colour: int = EmbedColours.DEFAULT.value,
	) -> None:
		"""
		Init for the base table view.

		Args:
			entries (list[EntryT]): List of a generic Entry Type.
			page (int): Page number of the view.
			page_size (int): The number of entries to show on the page.
			colour (int): Colour of the view's left side embed.
		"""

		# Run the standard layout view stuff.
		super().__init__()

		self.entries = entries
		self.page = page
		self.page_size = page_size
		self.total_pages = 1
		self.colour = colour
		self.show_info: bool = False

	@classmethod
	async def send(cls, destination: discord.abc.Messageable, *args, **kwargs) -> discord.Message:
		"""
		Send a message to the destination channel.

		Args:
			destination: Where to send message to.
			*args: Required arguments, including from child classes. e.g. BaseTableView adds columns and user_name.
			**kwargs: Keyword/optional arguments, including from child classes. e.g. PartyView adds party_stats.
		"""
		view = cls(*args, **kwargs)
		return await destination.send(view=view)

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

	@abstractmethod
	def _build_layout(self) -> None:
		raise NotImplementedError

	@abstractmethod
	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		raise NotImplementedError

	def _build_footer(self, container: discord.ui.Container) -> discord.ui.Container:
		"""Footer shows number of pages and given there's more than one page, will create page navigation."""
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(discord.ui.TextDisplay(f"-# Page {self.page} of {self.total_pages}"))

		if self.total_pages != 1:
			page_nav = discord.ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))
			container.add_item(page_nav)

		return container

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

	def refresh(self) -> None:
		self.clear_items()
		self._build_layout()
