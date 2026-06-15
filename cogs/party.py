import typing

import discord

from discord.ext import commands

from entities.view_data import Columns, get_args
from helpers import checks
from helpers.views import CompendiumView, ConfirmationView, MessageView
from queries import demon_queries, player_demons_queries
from shared_enums import DemonRegistration


class Party(commands.Cog):
	"""Cog for viewing and managing player parties."""

	def __init__(self, bot: commands.Bot):
		"""Init the Party cog with reference to bot instance and database classes."""
		self.bot = bot

	@checks.has_profile()
	@commands.command(name="party", aliases=["p"], help="Displays the player's current party.")
	async def party_command(self, ctx: commands.Context, *args: str) -> None:
		"""
		Command to display player's current party.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check party for.
		"""
		server = typing.cast(discord.Guild, ctx.guild)
		mentioned = None
		columns = list(Columns.PLAYER_DEFAULT)

		if args:
			mentioned, columns = get_args(args, server, columns)

		player = mentioned if mentioned is not None else ctx.author

		party_list = await player_demons_queries.check_party(player.id, server.id)
		sd_id = player_demons_queries.get_selected_demon_id(player.id, server.id)

		view = CompendiumView(player.name, party_list, columns, selected_demon_id=sd_id)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(name="release", aliases=["rel"], help="Release a demon from your party.")
	async def release_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		"""
		Command to release a demon from the player's party.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to release from the party. The * before it in the arguments
				allows for multi-word demon names.
		"""
		guild = typing.cast(discord.Guild, ctx.guild)
		player = ctx.author
		demon_name = demon_name.title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)

		if demon_id is None:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Check if demon is in party.
		in_party = await player_demons_queries.check_demon_registration(player.id, guild.id, demon_id)

		if in_party != DemonRegistration.IN_PARTY:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(f"Are you sure you want to release **{demon_name}**?", confirmLabel="Yes", denyLabel="No")
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		await player_demons_queries.set_demon_in_party(player.id, guild.id, demon_id, set_in_party=False)
		msg = MessageView(
			f"### Good-Bye...\n**{demon_name}** will have a happy life in a faraway forest."
			f"You will never see your **{demon_name}** again."
		)
		await ctx.send(view=msg)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Party(bot))
