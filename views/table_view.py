from typing import Generic, cast

import discord

from entities.comp_data import DemonEntry
from entities.item_data import ItemEntry
from entities.player_data import PartyStats
from entities.server_data import ServerStats
from entities.view_data import ColumnConfig
from shared_enums import Emotes
from views.common_view import BaseLayoutView, EntryT


class BaseTableView(BaseLayoutView, Generic[EntryT], discord.ui.LayoutView):
	"""Custom view for displaying things in a table format."""

	def __init__(
		self,
		user_name: str,
		entries: list[EntryT],
		columns: list[ColumnConfig],
		page: int = 1,
		colour: int = 0xE93700,
		filtered_race: str = "all",
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
		super().__init__(entries, page=page, colour=colour)

		self.user_name = user_name
		self.columns = columns
		self.filtered_race = filtered_race

		self.refresh()

	def _build_table_header(self, container: discord.ui.Container) -> discord.ui.Container:
		if len(self.entries) < 1:
			return container

		tab = "\u2003"
		header = ""

		for col in self.columns:
			header += f"{tab * col.header_tabs}{col.label:^{col.width}}"

		container.add_item(discord.ui.TextDisplay(f"-# {header}"))

		return container

	def _build_page_entry(self, container: discord.ui.Container, entry: EntryT) -> discord.ui.Container:
		tab = "\u2003"
		new_row = ""

		for col in self.columns:
			value = getattr(entry, col.key)

			if col.width == 0:
				new_row += Emotes.BLANK.value
				continue

			text = str(value).title()
			new_row += f"{tab}`{text:{col.align}{col.width}}`"

		container.add_item(discord.ui.TextDisplay(new_row))
		return container


class BaseCompendiumView(BaseTableView[DemonEntry]):
	class RaceSelect(discord.ui.Select):
		"""Custom select menu for filtering demons by race."""

		def __init__(self, races: list[str], selected: str) -> None:
			options = [discord.SelectOption(label="All", value="all")]
			sorted_races = sorted(races)

			for r in sorted_races:
				options.append(discord.SelectOption(label=r, value=r.lower()))

			super().__init__(placeholder=selected.title(), options=options)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a race is selected from the filter menu."""
			view = cast(BaseCompendiumView, self.view)
			view.filtered_race = self.values[0]
			view.page = 1
			view.total_pages = 1
			view.refresh()
			await interaction.response.edit_message(view=view)

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
		race_select = self.RaceSelect(list(races), selected=self.filtered_race)
		return discord.ui.ActionRow(race_select)

	def _get_filtered_entries(self) -> list[DemonEntry]:
		"""Filter entries by the race select dropdown."""

		page_entries = []

		for entry in self.entries:
			selected_race = entry.race.lower()

			# Check filtered_race against selected race and only add to page entries if it matches.
			if self.filtered_race == "all" or selected_race == self.filtered_race:
				page_entries.append(entry)

		return page_entries

	def _build_page_entry(
		self,
		container: discord.ui.Container,
		entry: DemonEntry,
		emote_override: Emotes | None = None,
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


class CompendiumView(BaseCompendiumView):
	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		# Draw the info button next to the title.
		info_button = self.InfoButton(self.show_info)
		section = discord.ui.Section(accessory=info_button)
		section.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Compendium"))
		container.add_item(section)

		if self.show_info:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

			container.add_item(
				discord.ui.TextDisplay(
					"-# - The Demonic Compendium is a list of every demon you have ever recruited."
					"\n-# - You can `>summon` a demon again from your Compendium for a fee."
					"\n-# - You can view other player's Compendiums by mentioning them or using their ID."
					"\n-# - A demon's Stored Rank will update as they get stronger."
				),
			)

			container.add_item(discord.ui.TextDisplay("-# **FILTER BY RACE**"))
			race_select = self._build_race_filter()
			container.add_item(race_select)

			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		else:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container


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

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		# Party stat information.
		container.add_item(
			discord.ui.TextDisplay(
				f"-# Number in Party: **{self.party_stats.size}** / **{self.party_stats.cap}** "
				f"• Average Rank: **{self.party_stats.average}**"
			)
		)

		# Note if player doesn't have a leader.
		if not self.selected_demon_id:
			container.add_item(
				discord.ui.TextDisplay("-# **NOTE:** No demon is leading your party. Use `>select` to choose a leader")
			)

		# Note if player has a full party.
		if self.party_stats.size >= self.party_stats.cap:
			container.add_item(
				discord.ui.TextDisplay("-# **NOTE:** Party is full. Use `>increase_party` to increase party's capacity.")
			)

		# Draw the info button next to the title.
		info_button = self.InfoButton(self.show_info)
		section = discord.ui.Section(accessory=info_button)
		section.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Party"))
		container.add_item(section)

		if self.show_info:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

			container.add_item(
				discord.ui.TextDisplay(
					"-# - The average demon rank controls the weight of your encounter's spawning rank."
					"\n-# - You can check details about your party's leader with `>leader` and swap them using `>select`."
					"\n-# - You can `>increase_party` slots for a fee, or `>release` demons to make space."
				),
			)

			container.add_item(discord.ui.TextDisplay("-# **FILTER BY RACE**"))
			race_select = self._build_race_filter()
			container.add_item(race_select)

			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		else:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _build_selected_demon_row(self, container: discord.ui.Container) -> discord.ui.Container:
		# Only render selected if first page and selected has been passed in.
		if self.selected_demon_id is None or self.page != 1:
			return container

		# Find the selected demon if it exists in the list.
		entry_ids = {entry.demon_id: entry for entry in self.entries}
		selected_demon = entry_ids.get(self.selected_demon_id)

		# Draw selected demon at the top of the list on the first page.
		if selected_demon:
			container = self._build_page_entry(container, selected_demon, emote_override=Emotes.KNOT)

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

	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)

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


class GemCollectionView(BaseTableView[ItemEntry]):
	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Gem Collection"))
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		return container


class InventoryView(BaseTableView[ItemEntry]):
	def _build_layout(self) -> None:
		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		container = self._build_table_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(discord.ui.TextDisplay(f"### {self.user_name}'s Item Collection"))
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		return container
