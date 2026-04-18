import discord
import typing

from cogs.demons import DemonQueries
from discord.ext import commands
from helpers import checks, players
from shared_enums import DemonRegistration, Emotes

## Constants
PAGE_SIZE = 5

class Compendium(commands.Cog):
	'''Cog for viewing and summoning from player compendiums.'''
	def __init__(self, bot: commands.Bot) -> None:
		'''Init the Compendium cog with reference to bot instance and database classes.'''
		self.bot = bot
		self.demon_db = DemonQueries()
		self.player_db = players.Players()


	@commands.command(name = 'compendium', aliases = ['comp', 'c'], help = "Displays the player's compendium.")
	async def compendium_command(self, ctx: commands.Context, mentioned: discord.Member | None = None) -> None:
		'''
		Command to display player's seen demons which is stored in their compendium.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check compendium for.
		'''
		guild = typing.cast(discord.Guild, ctx.guild)
		player = mentioned if mentioned is not None else ctx.author

		comp_list = await self.player_db.check_compendium(player.id, guild.id)
		view = CompendiumView(player.name, comp_list)
		await ctx.send(view = view)
	

	@checks.has_profile()
	@commands.command(name = 'summon', aliases = ['sum'], help = "Summon a demon from the player's compendium.")
	async def summon_command(self, ctx, *, demon_name) -> None:
		'''
		Command to summon a demon from the player's compendium into their party.
		TODO: Implement a cost to summoning.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to summon. The * before it in the arguments 
				allows for multi-word demon names.
		'''
		guild 		= typing.cast(discord.Guild, ctx.guild)
		player 		= ctx.author
		demon_name 	= demon_name.title()
		demon_id 	= self.demon_db.get_demon_id_by_name(demon_name)

		# Check if demon is in compendium before summoning to give a more informative message.
		in_comp = await self.player_db.check_demon_registration(
			player.id,
			guild.id,
			demon_id
		)		

		if in_comp == DemonRegistration.UNREGISTERED or demon_id == -1:
			await ctx.send(f"A demon with the name {demon_name} was not found in your compendium.")
			return
		
		if in_comp == DemonRegistration.IN_PARTY:
			await ctx.send(f"You already have {demon_name} in your party...")
			return

		if demon_id != -1:
			await self.player_db.set_demon_in_party(player.id, guild.id, demon_id, True)
			await ctx.send(f"You have summoned {demon_name} to your party...")
		

class CompendiumView(discord.ui.LayoutView):
	'''Custom view for displaying the player's viewed demons and hints at unseen ones.'''
	def __init__(
		self, 
		user_name: str, 
		list: list[dict], 
		page: int = 1, 
		colour: int = 0xE93700,
	) -> None:
		'''
		Init for the compendium view.
		
		Args:
			user_name (str): Name of the user whose compendium is being displayed.
			list (list[dict]): List of demons in the player's compendium. Each dict should include ID, name, race, personality, rank, and in_party.
			page (int): Current page number of the compendium view. Defaults to 1.
			colour (int): Colour of the compendium view.
			filtered_race (str): Race to filter the compendium view by. Defaults to 'all'.
		'''
		super().__init__()

		self.user_name = user_name
		self.list = list
		self.page = page
		self.colour = colour
		self.filtered_race = 'all'

		self._build_compendium_layout()

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
			f"-# {Emotes.BLANK.value}{tab * 3}Race{tab * 5}Name{tab * 4}Rank{tab * 3}Personality"
		))

		max_width_race = 8
		max_width_name = 12
		max_width_rank = 3
		max_width_pers = 12

		for entry in page_entries:
			_id, name, race, personality, rank, in_party = entry

			if self.filtered_race != 'all' and race.lower() != self.filtered_race:
				continue

			if rank is not None:
				emote = Emotes.ICON.value if in_party else Emotes.BLANK.value
				container.add_item(ui.TextDisplay(
					f"{emote}{tab}`{race:^{max_width_race}}`{tab}`{name:^{max_width_name}}`{tab}`{str(rank):>{max_width_rank}}`{tab}`{personality.title():^{max_width_pers}}`"
				))
			else:
				container.add_item(ui.TextDisplay(
					f"{Emotes.BLANK.value}{tab}`{'?????':^{max_width_race}}`{tab}`{'?????':^{max_width_name}}`{tab}`{'???':>{max_width_rank}}`{tab}`{'?????':^{max_width_pers}}`"
				))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f'-# Page {self.page} of {self.total_pages}'))
		container.add_item(page_nav)
		self.add_item(container)


	def _build_race_filter(self) -> discord.ui.ActionRow:
		'''
		Helper to build the race filter select menu. Gathers distinct races from the comp list
		and populates the options into the select menu.

		Returns:
			discord.ui.ActionRow: Action row containing the race filter select menu.
		'''
		# Set will prevent duplicates.
		races = set()
		for entry in self.list:
			race = entry[2]
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
		page_list = []

		for entry in self.list:
			selected_race = entry[2].lower()

			# Check filtered_race against selected race and only add to page list if it matches.
			if self.filtered_race == 'all' or selected_race == self.filtered_race:
				page_list.append(entry)

		self.total_pages 	= int(max(1, (len(page_list) + PAGE_SIZE - 1) / PAGE_SIZE))
		self.page		 	= max(1, min(self.page, self.total_pages))

		start_index	= (self.page - 1) * PAGE_SIZE
		end_index 	= start_index + PAGE_SIZE

		# Use delimiter to slice out entries.
		return page_list[start_index:end_index]


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Compendium(bot))
