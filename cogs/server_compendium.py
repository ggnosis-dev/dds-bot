import typing

import discord

from discord.ext import commands

from entities.view_data import Columns, get_args
from helpers import checks
from helpers.views import ConfirmationView, MessageView, ServerCompendiumView
from queries import demon_queries, player_demons_queries, server_demons_queries, server_level_queries
from shared_enums import DemonRegistration


class ServerCompendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		"""Init the Compendium cog with reference to bot instance and database classes."""
		self.bot = bot

	@commands.command(
		name="server_comp",
		aliases=["servcomp", "sc"],
		help="Displays the server's compendium. Can provide @player to see their loaned demons.",
	)
	async def server_comp_command(self, ctx: commands.Context, *args: str) -> None:
		server = typing.cast(discord.Guild, ctx.guild)
		columns = list(Columns.SERVER_DEFAULT)
		mentioned = None

		if args:
			columns, mentioned = get_args(args, server, columns)
			mentioned = mentioned.id if mentioned else None

		comp_list = await server_demons_queries.check_server_compendium(server.id, mentioned)

		# Because the server COMP only stores user IDs, we need to retrieve their names.
		for entry in comp_list:
			if entry.owner_id is not None:
				player = server.get_member(entry.owner_id)
				entry.owner = player.display_name if player else "Unknown"

		view = ServerCompendiumView(server.name, comp_list, columns)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(name="loan", help="Loan a demon to the server's compendium.")
	async def loan_command(self, ctx, *, demon_name) -> None:
		player = ctx.author
		server = typing.cast(discord.Guild, ctx.guild)
		demon_name = demon_name.title()
		demon = demon_queries.get_demon_by_name(demon_name)

		if demon is None:
			msg = MessageView(f"**{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Check if demon is in party.
		in_party = await player_demons_queries.check_demon_registration(player.id, server.id, demon.id)

		if in_party != DemonRegistration.IN_PARTY:
			msg = MessageView(f"**{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(
			f"Do you wish to loan your **{demon.race} {demon.name}** to the **{server.name}'s Compendium**?\n\n"
			f"-# You will not be able to use the demon again until taken back.",
			confirmLabel="Yes",
			denyLabel="No",
			colour=demon.colour,
		)
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		success = await server_demons_queries.add_demon_to_server_compendium(player.id, server.id, demon.id)

		# If a demon is already stored, check if they can overwrite it.
		if success is False:
			stored_demon = await server_demons_queries.get_single_serv_comp_demon(server.id, demon.id)
			stored_owner = typing.cast(discord.Member, self.bot.get_user(stored_demon.player_id))

			# If weaker, send message regarding that.
			if demon.rank <= stored_demon.stored_rank:
				msg = MessageView(
					f"**{stored_owner}**'s **{demon_name}** (Rank {stored_demon.stored_rank}) "
					f"is already in {server.name}'s Compendium."
				)
				await ctx.send(view=msg)
				return

			# If stronger, prompt to overwrite.
			view = ConfirmationView(
				f"**{stored_owner}** is already loaning their **{demon.name}** to **{server.name}'s Compendium**."
				"-# Do you wish to replace it? The demon will be returned to its owner.\n\n"
				"-# You will not be able to use the demon again until taken back.",
				confirmLabel="Replace",
				denyLabel="Cancel",
				colour=demon.colour,
			)
			result = await ConfirmationView.send_message(view, ctx)

			if result is False or result is None:
				return

			await server_demons_queries.replace_server_compendium_demon(
				player.id,
				server.id,
				demon.id,
			)

			# Add experience to the server's level.
			await server_level_queries.try_server_level_up(server.id, -stored_demon.stored_rank)
			await server_level_queries.try_server_level_up(server.id, demon.rank)

			msg = MessageView(
				f"Your **{demon.race} {demon.name}** (Rank {demon.rank}) has been sacrificed to **{server.name}'s "
				f"Compendium** for the time being."
				f"\n\n{stored_owner.mention}'s {demon.name} has been returned to its owner's COMP.",
				image=demon.profile_url,
				colour=demon.colour,
			)
			await ctx.send(view=msg)
			return

		# Add experience to the server's level.
		await server_level_queries.try_server_level_up(server.id, demon.rank)

		msg = MessageView(
			f"Your **{demon.race} {demon.name}** (Rank {demon.rank}) has been sacrificed to **{server.name}'s "
			f"Compendium** for the time being.",
			image=demon.profile_url,
			colour=demon.colour,
		)
		await ctx.send(view=msg)

	@checks.has_profile()
	@commands.command(name="return", help="Loan a demon to the server's compendium.")
	async def return_command(self, ctx, *, demon_name) -> None:
		player = ctx.author
		server = typing.cast(discord.Guild, ctx.guild)
		demon_name = demon_name.title()
		demon = demon_queries.get_demon_by_name(demon_name)

		if demon is None:
			msg = MessageView(f"**{demon_name}** was not found on loan...")
			await ctx.send(view=msg)
			return

		stored_demon = await server_demons_queries.get_single_serv_comp_demon(server.id, demon.id)

		if stored_demon is not None and player.id == stored_demon.player_id:
			view = ConfirmationView(
				f"Are you sure you want to retrieve **{demon.race} {demon.name}** (Rank {demon.rank}) "
				f"from **{server.name}'s Compendium**?",
				confirmLabel="Yes",
				denyLabel="No",
				colour=demon.colour,
			)
			result = await ConfirmationView.send_message(view, ctx)

			if result is False or result is None:
				return

			if await server_demons_queries.return_server_comp_demon(server.id, demon.id):
				# Remove the experience from the server's level.
				await server_level_queries.try_server_level_up(server.id, -stored_demon.stored_rank)

				msg = MessageView(
					f"**{demon.race} {demon.name}** has been returned to you.", demon.profile_url, demon.colour
				)
				await ctx.send(view=msg)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(ServerCompendium(bot))
