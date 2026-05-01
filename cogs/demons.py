from discord.ext import commands
from helpers import checks, demon_queries, players
from shared_enums import DemonRegistration


class Demon(commands.Cog):
	'''Cog for demon-related commands and functionality.'''
	def __init__(self, bot):
		self.bot = bot
		self.demon_db = demon_queries.DemonQueries()
		self.player_db = players.Players()


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


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Demon(bot))
