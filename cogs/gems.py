import typing

import discord

from discord.ext import commands

from entities.command_data import GEMS_COMMANDS, command_kwargs
from entities.demon_data import DemonData
from entities.view_data import Columns
from helpers import checks, gets
from queries import demon_queries, gem_queries, player_demons_queries
from views.common_view import MessageView
from views.table_view import GemCollectionView


class Gems(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message) -> None:
		"""
		Listener for player messages to track progress towards finding a gem.
		Only triggers if player has a profile.
		"""
		try:
			# Exit early if message is from bot or not in a server.
			if message.author.bot or message.guild is None:
				return

			ctx = await self.bot.get_context(message)

			# This check will exit if the player uses a proper command.
			if ctx.valid:
				return

			player_id, server_id = gets.get_player_server_ids(ctx)
			selected_demon_id = player_demons_queries.get_selected_demon_id(player_id, server_id)

			if selected_demon_id is None:
				return

			# Increase exp towards finding a gem.
			gem_found = gem_queries.increase_gems(player_id, server_id, selected_demon_id)

			if gem_found:
				try:
					d = typing.cast(DemonData, demon_queries.get_demon_by_id(selected_demon_id))
					view = MessageView(
						f"{message.author.mention}, your **{d.name}** has found a **{gem_found.title()}**!",
						d.profile_url,
						d.colour,
					)
					await message.channel.send(view=view)
				except Exception as e:
					print(f"ERROR: Failed to send gem found message: {e}")
		except Exception as e:
			print(f"WARN: Does not have correct permissions {e}")

	@commands.command(**command_kwargs(GEMS_COMMANDS, "gems"))
	async def gem_collection_command(self, ctx: commands.Context) -> None:
		"""View player's current gem collection."""
		player_id, server_id = gets.get_player_server_ids(ctx)
		collected_gems = gem_queries.get_player_gems(player_id, server_id)
		columns = list(Columns.ITEM_DEFAULT)

		view = GemCollectionView(ctx.author.name, collected_gems, columns)
		await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Gems(bot))
