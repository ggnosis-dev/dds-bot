import typing

from discord.ext import commands
from helpers import checks, demon_queries, player_queries
from helpers.view import MessageView
from shared_enums import DemonRegistration


class Demon(commands.Cog):
	'''Cog for demon-related commands and functionality.'''
	def __init__(self, bot):
		self.bot = bot
		self.demon_db = demon_queries.DemonQueries()
		self.player_db = player_queries.PlayerQueries()


	@checks.has_profile()
	@commands.command(name = 'select', aliases = ['s', 'sel'], description = "Select a demon to lead your party.")
	async def select_demon_command(self, ctx, *, demon_name: str) -> None:
		'''Select a demon to lead your party.'''
		player = ctx.author
		server = ctx.guild
		demon_name = demon_name.title()
		demon_id = self.demon_db.get_demon_id_by_name(demon_name)

		# Repeat the same message to avoid giving away whether a demon exists or not.
		if demon_id is None:
			await ctx.send(f"A **{demon_name}** is not in your party...")
			return

		# Check if in player's party.
		in_party = await self.player_db.check_demon_registration(
			player.id, 
			server.id, 
			demon_id
		)

		if in_party != DemonRegistration.IN_PARTY:
			await ctx.send(f"A **{demon_name}** is not in your party...")
			return

		self.player_db.set_selected_demon(ctx.author.id, ctx.guild.id, demon_id)
		await ctx.send(f"**{demon_name}** has been selected to lead your party!")


	@checks.has_profile()
	@commands.command(name = 'leader', aliases = ['selected'], description = 'Check which demon currently leads your party.')
	async def check_selected_demon_command(self, ctx) -> None:
		player = ctx.author
		server = ctx.guild

		d_id = self.player_db.get_selected_demon_id(player.id, server.id)

		if d_id is None:
			await ctx.send("There is currently no demon leading your party. Select one using `>select {Demon Name}`.")
			return
		
		d = typing.cast(demon_queries.DemonData, self.demon_db.get_demon_by_id(d_id))
		gem_progress = round(self.player_db.get_gem_progress(player.id, server.id, d.gem) / 10)
		progress_bar = '⬤ ' * gem_progress + '◯ ' * (10 - gem_progress)

		view = MessageView(
			f"**{d.race} {d.name}** currently leads your party.\n\n-# **Rank:** {d.rank}\n-# **Hunting:** {d.gem.title()}\n-# **Progress:** {progress_bar}", 
			d.image_url, 
			d.colour
		)
		await ctx.send(view = view)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Demon(bot))
