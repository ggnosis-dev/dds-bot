from discord.ext import commands

from entities.command_data import DEMONS_COMMANDS, command_kwargs
from helpers import checks, gets
from queries import demon_queries, gem_queries, player_demons_queries
from shared_enums import DemonRegistration, Unicode
from views.common_view import MessageView


class Demon(commands.Cog):
	"""Cog for demon-related commands and functionality."""

	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "select"))
	async def select_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		"""Select a demon to lead your party."""
		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_name = demon_name.title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)

		# Repeat the same message to avoid giving away whether a demon exists or not.
		if demon_id is None:
			await ctx.send(f"A **{demon_name}** is not in your party...")
			return

		# Check if in player's party.
		in_party = await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)

		if in_party != DemonRegistration.IN_PARTY:
			await ctx.send(f"A **{demon_name}** is not in your party...")
			return

		player_demons_queries.set_selected_demon(player_id, server_id, demon_id)
		await ctx.send(f"**{demon_name}** has been selected to lead your party!")

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "leader"))
	async def leader_command(self, ctx: commands.Context) -> None:
		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_id = await player_demons_queries.get_selected_demon_id(player_id, server_id)

		if demon_id is None:
			await ctx.send("There is currently no demon leading your party. Select one using `>select {demon}`.")
			return

		d = demon_queries.get_demon_by_id(demon_id)

		if d is None:
			raise RuntimeError("ERROR: leader_command | ID was found but DemonData was not.")

		# Get gem progress.
		gem_progress = round(gem_queries.get_gem_progress(player_id, server_id, d.id) / 10)
		progress_bar = f"{Unicode.FILLED_CIRCLE.value} " * gem_progress + f"{Unicode.UNFILLED_CIRCLE.value} " * (
			10 - gem_progress
		)

		# Get gems player can get with demon.
		gems = gem_queries.get_possible_gems(d.race)
		gem_text = "; ".join(gems).title()

		view = MessageView(
			(
				f"**{d.race} {d.name}** is currently leading your party.\n\n"
				f"-# **Rank:** {d.rank}\n"
				f"-# **Hunting:** {gem_text}\n"
				f"-# **Progress:** {progress_bar}"
			),
			d.design_data.profile_url,
			d.design_data.colour,
		)
		await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Demon(bot))
