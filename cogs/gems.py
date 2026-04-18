import discord

from discord.ext import commands
from helpers import checks, players 
from shared_enums import Emotes


class Gems(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.player_db = players.Players()


	@commands.command(name = 'gems', aliases = ['g'], description = "Displays the player's current gem collection.")
	async def gem_collection_command(self, ctx) -> None:
		'''View player's current gem collection.'''
		pass


	@checks.has_profile()
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message) -> None:
		'''
		Listener for player messages to track progress towards finding a gem.
		Only triggers if player has a profile.
		'''
		'''
		1. Each message will add to a gem hunt meter.
			1. Would it be easier to have rank add to the meter faster or have the meter determined by rank?
			2. Probably want to store this too so player's can change demons and not lose progress towards finding a gem.
		2. The selected demon's rank will influence how quick a gem is found.
			1. Need to create a method of selecting a demon.
			2. Add a DB entry for whether demon is selected. Could do a reference in the basic players table so to avoid a new column in player_demons that will be a bunch of 0s.
		3. Send a message when a gem is found.
		4. Update player gem table in DB.
		'''
		# Exit early if message is from bot or not in a server.
		if message.author.bot or message.guild is None:
			return
		
		ctx = await self.bot.get_context(message)

		# This check will exit if the player uses a proper command.
		if ctx.valid : return
		
		player_id = message.author.id
		guild_id = message.guild.id
		selected_demon_id = self.player_db.get_selected_demon_id(player_id, guild_id)
		
		if selected_demon_id is None : return
		
		exp = 10

		# Increase exp towards finding a gem.
		gem_found = await self.player_db.increase_gems(player_id, guild_id, selected_demon_id, exp)
		
		if gem_found:
			await message.channel.send(f"{message.author.mention} has found a gem!")


class GemCollectionView(discord.ui.View):

	def __init__(
		self, 
		user_name: str, 
		collected_gems: list[dict], 
		colour: int
	) -> None:
		'''
		View class for displaying a player's gem collection.

		Args:
			user_name (str): Name of the player whose collection is being displayed.
			gem_list (list[dict]): List of dictionaries which include gem name and quantity.
			colour (int): Colour for the view's accent.
		'''
		super().__init__()

		self.user_name = user_name
		self.collected_gems = collected_gems
		self.colour = colour

		self._build_gem_col_layout()


	def _build_gem_col_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		tab = '\u2003'

		container.add_item(ui.TextDisplay(f"### {self.user_name}'s Gem Collection"))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(
			f"-# {Emotes.BLANK.value}{tab * 3}Gemstone{tab * 5}Quantity")
		)

		max_width_name = 12
		max_width_qty = 3

		for entry in self.collected_gems:
			name, qty = entry
			# emote = Emotes[name].value
			emote = Emotes.ICON.value

			container.add_item(ui.TextDisplay(
				f"{emote}{tab}`{name:^{max_width_name}}`{tab}`{qty:>{max_width_qty}}`", 
			))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		self.add_item(container)
		

async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Gems(bot))
