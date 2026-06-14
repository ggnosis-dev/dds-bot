import typing

import discord

from discord.ext import commands

from helpers import checks
from helpers.views import Columns, CompendiumView, ConfirmationView, MessageView
from queries import demon_queries, player_queries
from shared_enums import DemonRegistration


class ServerCompendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		"""Init the Compendium cog with reference to bot instance and database classes."""
		self.bot = bot
		self.demon_db = demon_queries.DemonQueries()
		self.player_db = player_queries.PlayerQueries()

	@commands.command(name="server_comp", aliases=["servcomp", "sc"], help="Displays the server's compendium.")
	async def server_comp_command(self, ctx: commands.Context) -> None:
		server = typing.cast(discord.Guild, ctx.guild)

		comp_list = await self.player_db.check_server_compendium(server.id)

		for entry in comp_list:
			if entry.owner_id is not None:
				player = server.get_member(entry.owner_id)
				entry.owner = player.display_name if player else "Unknown"

		view = CompendiumView(server.name, comp_list, Columns.SERVER_DEFAULT)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(name="loan", help="Loan a demon to the server's compendium.")
	async def loan_command(self, ctx, *, demon_name) -> None:
		player = ctx.author
		server = typing.cast(discord.Guild, ctx.guild)
		demon_name = demon_name.title()
		demon = self.demon_db.get_demon_by_name(demon_name)

		if demon is None:
			msg = MessageView(f"**{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Check if demon is in party.
		in_party = await self.player_db.check_demon_registration(player.id, server.id, demon.id)

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

		success = await self.player_db.add_demon_to_server_compendium(player.id, server.id, demon.id)

		if success is False:
			stored_demon = await self.player_db.get_server_compendium_demon(server.id, demon.id)
			stored_owner = typing.cast(discord.Member, self.bot.get_user(stored_demon.player_id))

			# Ask to overwrite if stronger.
			if demon.rank <= stored_demon.stored_rank:
				msg = MessageView(
					f"**{stored_owner}**'s **{demon_name}** (Rank {stored_demon.stored_rank}) "
					f"is already in {server.name}'s Compendium."
				)
				await ctx.send(view=msg)
				return

			# Send a confirmation view.
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

			await self.player_db.replace_server_compendium_demon(player.id, server.id, demon.id)
			msg = MessageView(
				f"Your **{demon.race} {demon.name}** (Rank {demon.rank}) has been sacrificed to **{server.name}'s "
				f"Compendium** for the time being. {stored_owner.mention}'s {demon.name} has been returned to its COMP.",
				image=demon.profile_url,
				colour=demon.colour,
			)
			await ctx.send(view=msg)
			return

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
		demon = self.demon_db.get_demon_by_name(demon_name)

		if demon is None:
			msg = MessageView(f"**{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		stored_demon = await self.player_db.get_server_compendium_demon(server.id, demon.id)

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

			if await self.player_db.return_server_comp_demon(server.id, demon.id):
				msg = MessageView(
					f"**{demon.race} {demon.name}** has been returned to you.", demon.profile_url, demon.colour
				)
				await ctx.send(view=msg)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(ServerCompendium(bot))
