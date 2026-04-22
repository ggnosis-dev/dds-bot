import sqlite3
import typing

from cogs.demons import DemonData, DemonQueries
from discord.ext import commands
from helpers import checks, item_queries, players



class Items(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.item_queries = item_queries.ItemQueries()
		self.player_queries = players.Players()
		self.demon_queries = DemonQueries()


	@checks.has_profile()
	@commands.command(name = 'use', aliases = ['u'], description = "Use an item on a demon.")
	async def use_item_command(self, ctx, *, item_name: str) -> None:
		'''Use an item on a demon.'''
		player = ctx.author
		server = ctx.guild
		item_id = self.item_queries.get_item_id_by_name(item_name)
		
		if item_id is None:
			await ctx.send(f"The item '{item_name}' does not exist...")
			return

		if self.item_queries.get_player_has_item(player.id, server.id, item_id) == False:
			await ctx.send(f"You don't have any {item_name} in your inventory.")
			return
		
		selected_demon_id = self.player_queries.get_selected_demon_id(player.id, server.id)
		
		if selected_demon_id is None:
			await ctx.send("You don't have a demon selected. Use `>select` to choose a demon first.")
			return
		
		if self.item_queries.use_incense(
			player.id, 
			server.id, 
			selected_demon_id,
			item_id
		):
			demon_data = typing.cast(DemonData, self.demon_queries.get_demon_by_id(selected_demon_id))
			await ctx.send(f"{player.mention} used {item_name} on {demon_data.name}! Their stored rank has increased by 3.")


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Items(bot))
