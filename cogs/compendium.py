import discord

from cogs.demons import Demons
from cogs.players import Players
from discord.ext import commands
from shared_enums import DemonRegistration, Emotes


class Compendium(commands.Cog):
	'''Cog for viewing and summoning from player compendiums.'''
	def __init__(self, bot: commands.Bot) -> None:
		'''Init the Compendium cog with reference to bot instance and database classes.'''
		self.bot = bot
		self.demon_db = Demons()
		self.player_db = Players()


	@commands.command(name = 'compendium', aliases = ['comp', 'c'], help = "Displays the player's compendium.")
	async def compendium_command(self, ctx: commands.Context, user_id: int | None = None) -> None:
		'''
		Command to display player's seen demons which is stored in their compendium.

		Args:
			ctx (discord.Context): Context of the command call.
			user_id (int | None): Optional user ID to check compendium for.
		'''
		if ctx.guild is None : return

		server_id = ctx.guild.id

		if user_id is None : user_id = ctx.author.id

		comp_list = await self.player_db.check_compendium(user_id, server_id)
		view = CompendiumView(ctx.author.name, comp_list)
		await ctx.send(view = view)
	

	@commands.command(name = 'summon', aliases = ['s'], help = "Summon a demon from the player's compendium.")
	async def summon_command(self, ctx, *, demon_name) -> None:
		'''
		Command to summon a demon from the player's compendium into their party.
		TODO: Implement a cost to summoning.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to summon. The * before it in the arguments 
				allows for multi-word demon names.
		'''
		if ctx.guild is None : return
		
		demon_name = demon_name.title()
		demon_id = self.demon_db.get_demon_id_by_name(demon_name)	# type: ignore

		# Check if demon is in compendium before summoning to give a more informative message.
		in_comp = await self.player_db.check_demon_registration(	# type: ignore
			ctx.author.id,
			ctx.guild.id,
			demon_id
		)		

		if in_comp == DemonRegistration.UNREGISTERED or demon_id == -1:
			await ctx.send(f"A demon with the name {demon_name} was not found in your compendium.")
			return
		
		if in_comp == DemonRegistration.IN_PARTY:
			await ctx.send(f"You already have {demon_name} in your party...")
			return

		if demon_id != -1:
			await self.player_db.set_demon_in_party(ctx.author.id, ctx.guild.id, demon_id, True)		# type: ignore
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
		'''Custom select menu for filtering demons by race'''
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
			if not isinstance(self.view, CompendiumView):
				return
			
			view: CompendiumView = self.view
			view.filtered_race = self.values[0]
			view.clear_items()
			view._build_compendium_layout()
			await interaction.response.edit_message(view = view)


	def _build_compendium_layout(self) -> None:
		'''Function to build the compendium view layout.'''
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		race_select = self._build_race_filter()
		
		container.add_item(ui.TextDisplay(f"### {self.user_name}'s Compendium"))
		container.add_item(race_select)
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		for entry in self.list:
			_id, name, race, personality, rank, in_party = entry

			if self.filtered_race != 'all' and race.lower() != self.filtered_race:
				continue

			# This will exist if the player has encountered.
			if rank is not None:
				emote = Emotes.ICON.value if in_party else Emotes.BLANK.value

				container.add_item(ui.TextDisplay(
					f"{emote}\u2003\u2003{race}\u2003\u2003{name}\u2003\u2003\u2003\u2003`{rank}`\u2003\u2003{personality.title()}", 
				))
			else:
				container.add_item(ui.TextDisplay(
					f"{Emotes.BLANK.value}\u2003\u2003{race}\u2003\u2003?????\u2003\u2003\u2003\u2003`???`\u2003\u2003?????", 
				))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f'-# Page {self.page}'))
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



async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Compendium(bot))
