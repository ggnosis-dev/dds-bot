import typing

import discord

from discord.ext import commands

from helpers import checks
from helpers.views import MessageView
from queries import gem_queries, player_queries
from queries.demon_queries import DemonData, DemonQueries
from shared_enums import Emotes


class Gems(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.player_db = player_queries.PlayerQueries()

	@checks.has_profile()
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message) -> None:
		"""
		Listener for player messages to track progress towards finding a gem.
		Only triggers if player has a profile.
		"""
		# Exit early if message is from bot or not in a server.
		if message.author.bot or message.guild is None:
			return

		ctx = await self.bot.get_context(message)

		# This check will exit if the player uses a proper command.
		if ctx.valid:
			return

		player_id = message.author.id
		guild_id = message.guild.id
		selected_demon_id = self.player_db.get_selected_demon_id(player_id, guild_id)

		if selected_demon_id is None:
			return

		# Increase exp towards finding a gem.
		gem_found = await gem_queries.increase_gems(player_id, guild_id, selected_demon_id)

		if gem_found:
			try:
				d = typing.cast(DemonData, DemonQueries().get_demon_by_id(selected_demon_id))
				view = MessageView(
					f"{message.author.mention}, your **{d.name}** has found a **{d.gem.title()}**!",
					d.profile_url,
					d.colour,
				)
				await message.channel.send(view=view)
			except Exception as e:
				print(f"ERROR: Failed to send gem found message: {e}")

	@commands.command(name="gems", aliases=["g"], description="Displays the player's current gem collection.")
	async def gem_collection_command(self, ctx) -> None:
		"""View player's current gem collection."""
		player_id = ctx.author.id
		server_id = ctx.guild.id

		collected_gems = gem_queries.get_player_gems(player_id, server_id)
		view = GemCollectionView(ctx.author.name, collected_gems)
		await ctx.send(view=view)


class GemCollectionView(discord.ui.LayoutView):
	def __init__(self, user_name: str, collected_gems: list[tuple], colour: int = 0xE93700) -> None:
		"""
		View class for displaying a player's gem collection.

		Args:
			user_name (str): Name of the player whose collection is being displayed.
			gem_list (list[dict]): List of dictionaries which include gem name and quantity.
			colour (int): Colour for the view's accent.
		"""
		super().__init__()

		self.user_name = user_name
		self.collected_gems = collected_gems
		self.colour = colour

		self._build_gem_collection_layout()

	def _build_gem_collection_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)
		tab = "\u2003"

		container.add_item(ui.TextDisplay(f"### {self.user_name} Gems Collection"))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f"-# {Emotes.BLANK.value}{tab * 3}Gemstone{tab * 3}Quantity"))

		max_width_name = 12
		max_width_qty = 3

		for entry in self.collected_gems:
			name, qty = entry
			# emote = Emotes[name].value
			emote = Emotes.BLANK.value

			container.add_item(
				ui.TextDisplay(
					f"{emote}{tab}`{name.title():^{max_width_name}}`{tab * 2}`{qty:>{max_width_qty}}`",
				)
			)

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		self.add_item(container)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Gems(bot))
