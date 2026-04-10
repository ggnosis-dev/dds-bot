import discord

from cogs.demons import Demons
from cogs.players import Players
from discord.ext import commands
from shared_enums import DemonRegistration, Emotes


class Party(commands.Cog):
	'''Cog for viewing and managing player parties.'''
	def __init__(self, bot: commands.Bot):
		'''Init the Party cog with reference to bot instance and database classes.'''
		self.bot = bot
		self.demon_db = Demons()
		self.player_db = Players()


	@commands.command(name = 'party', aliases = ['p'], help = "Displays the player's current party.")
	async def party_command(self, ctx: commands.Context, user_id: int | None = None) -> None:
		'''
		Command to display player's current party.

		Args:
			ctx (discord.Context): Context of the command call.
			user_id (int | None): Optional user ID to check party for.
		'''
		if ctx.guild is None : return

		server_id = ctx.guild.id

		if user_id is None : user_id = ctx.author.id

		party_list = await self.player_db.check_party(user_id, server_id)							# type: ignore
		view = PartyView(ctx.author.name, party_list)
		await ctx.send(view = view)


	@commands.command(name = 'release', aliases = ['r'], help = "Release a demon from your party.")
	async def release_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		'''
		Command to release a demon from the player's party.
		
		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to release from the party. The * before it in the arguments 
				allows for multi-word demon names.
		'''
		if ctx.guild is None : return
		
		# Turn demon name to Title Case and get its ID.
		demon_name = demon_name.title()
		demon_id = self.demon_db.get_demon_id_by_name(demon_name)

		# Check if demon is in party before release to give a more informative message.
		in_party = await self.player_db.check_demon_registration(							# type: ignore
			ctx.author.id, 
			ctx.guild.id, 
			demon_id
		)

		if in_party != DemonRegistration.IN_PARTY or demon_id == -1:
			await ctx.send(f"The demon {demon_name} was not found in your party. Did you spell their name correctly?")
			return

		await self.player_db.set_demon_in_party(											# type: ignore
			ctx.author.id, 
			ctx.guild.id, 
			demon_id, 
			party_add = False
		)				
		await ctx.send(f"### Good-Bye...\n{demon_name} will have a happy life in a faraway forest. You will never see your {demon_name} again.")
	

class PartyView(discord.ui.LayoutView):
	'''Custom view for displaying the player's party.'''
	def __init__(
		self, 
		user_name: str, 
		list: list[dict], 
		page: int = 1, 
		colour: int = 0xE93700
	) -> None:
		'''
		Init for the party view. Builds the layout based on whether the player's party is empty or not.
		
		Args:
			user_name (str): Name of the user whose party is being displayed.
			list (list[dict]): List of demons in the player's party. Each dict should include ID, name, race, and stored_rank.
			page (int): Current page number of the party view. Defaults to 1.
			colour (int): Colour of the party view.
		'''
		super().__init__()

		self.user_name = user_name
		self.list = list
		self.page = page
		self.colour = colour

		self._build_party_layout() if list else self._build_party_empty_layout()


	def _build_party_layout(self) -> None:
		'''Function to build the party view layout.'''
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		
		container.add_item(ui.TextDisplay(f"### {self.user_name}'s Party"))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		for entry in self.list:
			_id, name, race, rank = entry

			container.add_item(ui.TextDisplay(
				f"{Emotes.ICON.value}\u2003\u2003{race}\u2003\u2003{name}\u2003\u2003\u2003\u2003`{rank}`", 
			))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f'-# Page {self.page}'))

		self.add_item(container)


	def _build_party_empty_layout(self) -> None:
		'''Function to build the party view layout when it's empty.'''
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		container.add_item(ui.TextDisplay(f'Your party is empty!'))
		self.add_item(container)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Party(bot))
