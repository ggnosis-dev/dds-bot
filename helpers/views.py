import asyncio
import discord
import typing

from dataclasses import dataclass
from helpers.player_queries import DemonEntry
from shared_enums import Emotes


COMP_PAGE_SIZE = 5


class MessageView(discord.ui.LayoutView):
	def __init__(self, 
		message: str,
		image: str | None = None,
		colour: int = 0xE93700,
	):
		super().__init__()
		self.message = message
		self.colour = colour
		self.image = image
		self._build_layout()


	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)

		if self.image is not None:
			section = ui.Section(accessory = ui.Thumbnail(media = self.image))
			section.add_item(ui.TextDisplay(self.message))
			container.add_item(section)
		else:
			container.add_item(ui.TextDisplay(self.message))

		self.add_item(container)


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


@dataclass
class ColumnConfig:
	# Key should match the database column's name.
	key: str
	label: str
	width: int
	align: str = '^'
	header_tabs: int = 1

class CompendiumView(discord.ui.LayoutView):
	'''Custom view for displaying the player's viewed demons and hints at unseen ones.'''
	def __init__(
		self, 
		user_name: str, 
		entries: list[DemonEntry], 
		columns: list[ColumnConfig],
		page: int = 1, 
		colour: int = 0xE93700,
	) -> None:
		'''
		Init for the compendium view.
		
		Args:
			user_name (str): Name of the user whose compendium is being displayed.
			entries (list[dict]): List of demons in the player's compendium. Each dict should include ID, name, race, personality, rank, and in_party.
			page (int): Current page number of the compendium view. Defaults to 1.
			colour (int): Colour of the compendium view.
			filtered_race (str): Race to filter the compendium view by. Defaults to 'all'.
		'''
		super().__init__()

		self.user_name = user_name
		self.entries = entries
		self.columns = columns
		self.page = page
		self.colour = colour
		self.filtered_race = 'all'

		self._build_layout()

	class RaceSelect(discord.ui.Select):
		'''Custom select menu for filtering demons by race.'''
		def __init__(self, races: list[str]) -> None:
			options = [discord.SelectOption(label = 'All', value = 'all')]

			sorted_races = sorted(races)
			for r in sorted_races:
				options.append(discord.SelectOption(label = r, value = r.lower()))

			super().__init__(
				placeholder = 'Filter By Race',
				options = options
			)


		async def callback(self, interaction: discord.Interaction) -> None:
			'''Callback for when a race is selected from the filter menu.'''
			view = typing.cast(CompendiumView, self.view)
			view.filtered_race = self.values[0]
			view.page = 1
			view.total_pages = 1
			view.clear_items()
			view._build_compendium_layout()
			await interaction.response.edit_message(view = view)


	class PageButton(discord.ui.Button):
		'''Custom button for navigating between pages of the compendium view.'''
		def __init__(self, direction: str) -> None:
			if direction == 'prev':
				super().__init__(label = '<', style = discord.ButtonStyle.primary)
			elif direction == 'next':
				super().__init__(label = '>', style = discord.ButtonStyle.primary)
			else:
				raise ValueError("ERROR: Direction must be 'prev' or 'next'.")


		async def callback(self, interaction: discord.Interaction) -> None:
			'''Callback for when a page navigation button is clicked. Allows wrapping around the pages.'''			
			view = typing.cast(CompendiumView, self.view)

			if self.label == '<':
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == '>':
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			view.clear_items()
			view._build_compendium_layout()
			await interaction.response.edit_message(view = view)


	def _build_layout(self) -> None:
		print("HERE")
		ui 				= discord.ui
		container 		= ui.Container(accent_color = self.colour)
		tab 			= '\u2003'
		race_select 	= self._build_race_filter()
		page_entries	= self._get_page_entries()

		container.add_item(ui.TextDisplay(f"### {self.user_name}'s Compendium"))
		container.add_item(race_select)
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		header = ''
		for col in self.columns:
			header += f"{tab * col.header_tabs}{col.label:^{col.width}}"
		container.add_item(ui.TextDisplay(f"-# {header}"))

		print(page_entries)
		for entry in page_entries:
			new_row = ''

			for col in self.columns:
				value = getattr(entry, col.key)

		self.add_item(container)


	def _build_compendium_layout(self) -> None:
		'''Function to build the compendium view layout.'''
		ui 				= discord.ui
		container 		= ui.Container(accent_color = self.colour)
		tab 			= '\u2003'
		race_select 	= self._build_race_filter()
		page_entries	= self._get_page_entries()
		page_nav 		= ui.ActionRow(self.PageButton('prev'), self.PageButton('next'))
		
		container.add_item(ui.TextDisplay(f"### {self.user_name}'s Compendium"))
		container.add_item(race_select)
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(
			f"-# {Emotes.BLANK.value}{tab * 3}Race{tab * 5}Name{tab * 4}Rank{tab * 3}Gemstone{tab * 4}Personality"
		))

		max_width_race = 8
		max_width_name = 12
		max_width_num = 3
		max_width_pers = 12

		for entry in page_entries:
			_id, name, race, personality, rank, in_party, gem = entry

			if self.filtered_race != 'all' and race.lower() != self.filtered_race:
				continue

			if rank is not None:
				emote = Emotes.ICON.value if in_party else Emotes.BLANK.value
				container.add_item(ui.TextDisplay(
					f"{emote}{tab}`{race:^{max_width_race}}`{tab}`{name:^{max_width_name}}`{tab}`{str(rank):>{max_width_num}}`{tab}`{gem.title():^{max_width_pers}}`{tab}`{personality.title():^{max_width_pers}}`"
				))
			else:
				container.add_item(ui.TextDisplay(
					f"{Emotes.BLANK.value}{tab}`{'?????':^{max_width_race}}`{tab}`{'?????':^{max_width_name}}`{tab}`{'???':>{max_width_num}}`{tab}`{'?????':^{max_width_pers}}`{tab}`{'?????':^{max_width_pers}}`"
				))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f'-# Page {self.page} of {self.total_pages}'))
		container.add_item(page_nav)
		self.add_item(container)


	def _build_race_filter(self) -> discord.ui.ActionRow:
		'''
		Helper to build the race filter select menu. Gathers distinct races from the comp entries
		and populates the options into the select menu.

		Returns:
			discord.ui.ActionRow: Action row containing the race filter select menu.
		'''
		# Set will prevent duplicates.
		races = set()
		for entry in self.entries:
			race = entry.race
			races.add(race)
		race_select = self.RaceSelect(list(races))
		return discord.ui.ActionRow(race_select)


	def _get_page_entries(self) -> list[dict]:
		'''
		Helper function to get the entries to be displayed on the current page of the compendium view.
		Sets self.total_pages based on the number of entries after filtering.

		Returns:
			list[dict]: List of demon entries to be displayed on the current page.
		'''
		page_entries = []

		for entry in self.entries:
			selected_race = entry.race.lower()

			# Check filtered_race against selected race and only add to page entries if it matches.
			if self.filtered_race == 'all' or selected_race == self.filtered_race:
				page_entries.append(entry)

		self.total_pages 	= int(max(1, (len(page_entries) + COMP_PAGE_SIZE - 1) / COMP_PAGE_SIZE))
		self.page		 	= max(1, min(self.page, self.total_pages))

		start_index	= (self.page - 1) * COMP_PAGE_SIZE
		end_index 	= start_index + COMP_PAGE_SIZE

		# Use delimiter to slice out entries.
		return page_entries[start_index:end_index]
