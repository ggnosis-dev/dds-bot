"""
Things to do:
	- Make a "Filters" button on the compendium views that open up the filter dropdown
		- Extend this to include the column options maybe?
		- Definitely good for sorting.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

import discord

from entities.comp_data import DemonEntry
from entities.item_data import GemEntry
from entities.player_data import PartyStats
from entities.server_data import ServerStats
from entities.view_data import COMP_PAGE_SIZE, ColumnConfig
from shared_enums import Emotes

T = TypeVar("T")


class BaseTableView(ABC, Generic[T], discord.ui.LayoutView):
	"""Custom view for displaying the player's viewed demons and hints at unseen ones."""

	def __init__(
		self,
		user_name: str,
		entries: list[T],
		columns: list[ColumnConfig],
		page: int = 1,
		colour: int = 0xE93700,
	) -> None:
		"""
		Init for the compendium view.

		Args:
			user_name (str): Name of the user whose compendium is being displayed.
			entries (list[dict]): List of demons in the player's compendium.
			page (int): Current page number of the compendium view. Defaults to 1.
			colour (int): Colour of the compendium view.
			filtered_race (str): Race to filter the compendium view by. Defaults to 'all'.
		"""
		super().__init__()

		self.user_name = user_name
		self.entries = entries
		self.columns = columns
		self.page = page
		self.colour = colour
		self.total_pages = 1
		self.filtered_race = "all"

		self._build_layout()

	class RaceSelect(discord.ui.Select):
		"""Custom select menu for filtering demons by race."""

		def __init__(self, races: list[str]) -> None:
			options = [discord.SelectOption(label="All", value="all")]
			sorted_races = sorted(races)

			for r in sorted_races:
				options.append(discord.SelectOption(label=r, value=r.lower()))

			super().__init__(placeholder="Filter By Race", options=options)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a race is selected from the filter menu."""
			view = cast(BaseCompendiumView, self.view)
			view.filtered_race = self.values[0]
			view.page = 1
			view.total_pages = 1
			view.clear_items()
			view._build_layout()
			await interaction.response.edit_message(view=view)

	class PageButton(discord.ui.Button):
		"""Custom button for navigating between pages of the compendium view."""

		def __init__(self, direction: str) -> None:
			if direction == "prev":
				super().__init__(label="<", style=discord.ButtonStyle.primary)
			elif direction == "next":
				super().__init__(label=">", style=discord.ButtonStyle.primary)
			else:
				raise ValueError("ERROR: Direction must be 'prev' or 'next'.")

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a page navigation button is clicked. Allows wrapping around the pages."""
			view = cast(BaseCompendiumView, self.view)

			if self.label == "<":
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == ">":
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			view.clear_items()
			view._build_layout()
			await interaction.response.edit_message(view=view)

	@abstractmethod
	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		pass

	@abstractmethod
	def _build_layout(self) -> None:
		pass

	def _build_table_header(self, container: discord.ui.Container) -> discord.ui.Container:
		tab = "\u2003"
		header = ""

		for col in self.columns:
			header += f"{tab * col.header_tabs}{col.label:^{col.width}}"

		container.add_item(discord.ui.TextDisplay(f"-# {header}"))

		return container

	def _build_page_entry(
		self,
		container: discord.ui.Container,
		entry: DemonEntry,
		emote_override=None,
	) -> discord.ui.Container:
		tab = "\u2003"
		new_row = ""

		for col in self.columns:
			value = getattr(entry, col.key)

			# This will be an emote column if width is 0.
			if col.width == 0:
				if emote_override:
					new_row += emote_override.value
				elif entry.in_party:
					new_row += Emotes.ICON.value
				else:
					new_row += Emotes.BLANK.value
				continue

			# When in_party is none, the player hasn't seen the demon before so show hint for it.
			if entry.is_unseen:
				# If column align is right, it's a value. Show less question marks.
				placeholder = "???" if col.align == ">" else "?????"
				new_row += f"{tab}`{placeholder:{col.align}{col.width}}`"

			else:
				# Only use title case if it's not a player's name.
				text = str(value).title() if not entry.owner else value
				new_row += f"{tab}`{text:{col.align}{col.width}}`"

		container.add_item(discord.ui.TextDisplay(new_row))

		return container

	def _build_footer(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(discord.ui.TextDisplay(f"-# Page {self.page} of {self.total_pages}"))

		if self.total_pages != 1:
			page_nav = discord.ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))
			container.add_item(page_nav)

		return container


class BaseCompendiumView(BaseTableView[DemonEntry]):
	def _build_race_filter(self) -> discord.ui.ActionRow:
		"""
		Helper to build the race filter select menu. Gathers distinct races from the comp entries
		and populates the options into the select menu.

		Returns:
			discord.ui.ActionRow: Action row containing the race filter select menu.
		"""
		# Set will prevent duplicates.
		races = set()
		for entry in self.entries:
			race = entry.race
			races.add(race)
		race_select = self.RaceSelect(list(races))
		return discord.ui.ActionRow(race_select)

	def _get_page_entries(self) -> list[DemonEntry]:
		"""
		Helper function to get the entries to be displayed on the current page of the compendium view.
		Sets self.total_pages based on the number of entries after filtering.

		Returns:
			list[dict]: List of demon entries to be displayed on the current page.
		"""
		page_entries = []

		for entry in self.entries:
			selected_race = entry.race.lower()

			# Check filtered_race against selected race and only add to page entries if it matches.
			if self.filtered_race == "all" or selected_race == self.filtered_race:
				page_entries.append(entry)

		self.total_pages = int(max(1, (len(page_entries) + COMP_PAGE_SIZE - 1) / COMP_PAGE_SIZE))
		self.page = max(1, min(self.page, self.total_pages))

		start_index = (self.page - 1) * COMP_PAGE_SIZE
		end_index = start_index + COMP_PAGE_SIZE

		# Use delimiter to slice out entries.
		return page_entries[start_index:end_index]


class CompendiumView(BaseCompendiumView):
	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Compendium"))

		race_select = self._build_race_filter()
		container.add_item(race_select)

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)


class PartyView(BaseCompendiumView):
	def __init__(
		self,
		*args,
		selected_demon_id: int | None = None,
		party_stats: PartyStats,
		**kwargs,
	) -> None:
		self.selected_demon_id = selected_demon_id
		self.party_stats = party_stats
		super().__init__(*args, **kwargs)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Party"))

		# Party stat information.
		container.add_item(
			discord.ui.TextDisplay(
				f"-# Number in Party: **{self.party_stats.size}** / **{self.party_stats.cap}** "
				f"• Average Rank: **{self.party_stats.average}**"
			)
		)

		# Mention if player doesn't have a leader.
		if not self.selected_demon_id:
			container.add_item(discord.ui.TextDisplay("-# No demon is leading your party. Use `>select` to choose a leader"))

		if self.party_stats.size >= self.party_stats.cap:
			container.add_item(
				discord.ui.TextDisplay("-# Party is full. Use `>increase_party` to increase party's capacity.")
			)

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		container = self._build_selected_demon_row(container)

		for entry in page_entries:
			if entry.demon_id == self.selected_demon_id:
				continue

			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_selected_demon_row(self, container: discord.ui.Container) -> discord.ui.Container:
		# Only render selected if first page and selected has been passed in.
		if self.selected_demon_id is None or self.page != 1:
			return container

		# Find the selected demon if it exists in the list.
		entry_ids = {entry.demon_id: entry for entry in self.entries}
		selected_demon = entry_ids.get(self.selected_demon_id)

		# Draw selected demon at the top of the list on the first page.
		if selected_demon:
			container = self._build_page_entry(container, selected_demon, emote_override=Emotes.ONE)

		return container


class ServerCompendiumView(BaseCompendiumView):
	def __init__(
		self,
		*args,
		server_stats: ServerStats,
		**kwargs,
	) -> None:
		self.server_stats = server_stats
		super().__init__(*args, **kwargs)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(
			discord.ui.TextDisplay(
				f"-# **Server Level: {self.server_stats.level} | Server Experience: {self.server_stats.total_xp}**"
			)
		)
		container.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Server Compendium"))

		# Average rank/Weighted rank.
		if self.page == 1:
			container.add_item(discord.ui.TextDisplay("-# Loan your demon by using `>loan`."))
			container.add_item(
				discord.ui.TextDisplay("-# Use `>server_stats` to see detailed information on server level and experience.")
			)

		race_select = self._build_race_filter()
		container.add_item(race_select)

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)
