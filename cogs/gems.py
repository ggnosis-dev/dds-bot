import discord

from discord.ext import commands

from shared_enums import Emotes


class Gems(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = 'gems', aliases = ['g'], description = "Displays the player's current gem collection.")
	async def gem_collection_command(self, ctx) -> None:
		'''View player's current gem collection.'''
		pass

	@commands.Cog.listener()
	async def on_message(self, message):
		'''Listener for player messages to track progress towards finding a gem.'''
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
		pass


class GemCollectionView(discord.ui.View):

	def __init__(self, user_name: str, gem_list: list[dict], colour: int) -> None:
		'''
		View class for displaying a player's gem collection.

		Args:
			user_name (str): Name of the player whose collection is being displayed.
			gem_list (list[dict]): List of dictionaries which include gem name and quantity.
			colour (int): Colour for the view's accent.
		'''
		super().__init__()

		self.user_name = user_name
		self.gem_list = gem_list
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

		for entry in self.gem_list:
			name, qty = entry
			# emote = Emotes[name].value
			emote = Emotes.ICON.value

			container.add_item(ui.TextDisplay(
				f"{emote}{tab}`{name:^{max_width_name}}`{tab}`{qty:>{max_width_qty}}`", 
			))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		self.add_item(container)
		

