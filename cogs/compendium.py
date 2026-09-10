import asyncio

from discord.ext import commands

from entities.command_data import COMPENDIUM_COMMANDS, command_kwargs
from entities.view_data import Columns, get_args
from helpers import checks, costs, gets
from helpers.messages import CompendiumMsg
from queries import currency_queries, demon_queries, player_demons_queries
from shared_enums import DemonRegistration
from views.common_view import ConfirmationView, MessageView
from views.demon_entry_view import DemonEntryBrowser
from views.table_view import CompendiumView


class Compendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@commands.command(**command_kwargs(COMPENDIUM_COMMANDS, "compendium"))
	async def compendium_command(self, ctx: commands.Context, *args: str) -> None:
		"""Command to display a player's seen demons which is stored in their compendium."""
		player, server = gets.get_player_server(ctx)
		columns = list(Columns.COMP_DEFAULT)
		mentioned = None

		if args:
			columns, mentioned = get_args(args, server, columns)
		need_gems = Columns.GEMS in columns

		# Swap player to the mentioned player if it was provided.
		player = mentioned if mentioned is not None else player
		comp_entries = await player_demons_queries.check_compendium(player.id, server.id, need_gems)

		await CompendiumView.send(
			ctx.channel,
			comp_entries,
			columns,
			player.name,
		)

	@checks.has_profile()
	@commands.command(**command_kwargs(COMPENDIUM_COMMANDS, "summon"))
	async def summon_command(self, ctx: commands.Context, *, demon_name: str | None) -> None:
		"""Command to summon a demon from the player's compendium into their party."""

		if demon_name is None:
			await MessageView.send(ctx.channel, CompendiumMsg.no_input_given(COMPENDIUM_COMMANDS["summon"]))
			return

		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_name = demon_name.title()
		demon = await demon_queries.get_demon_by_name(player_id, server_id, demon_name)

		if demon is None:
			await MessageView.send(ctx.channel, CompendiumMsg.not_in_comp(demon_name))
			return

		# Check if party has space.
		if not player_demons_queries.get_party_has_space(player_id, server_id):
			await MessageView.send(ctx.channel, CompendiumMsg.party_full())
			return

		# Check if demon is in compendium before summoning to give a more informative message.
		in_comp = await player_demons_queries.check_demon_registration(player_id, server_id, demon.id)

		if in_comp == DemonRegistration.UNREGISTERED:
			await MessageView.send(ctx.channel, CompendiumMsg.not_in_comp(demon_name))
			return

		if in_comp in (DemonRegistration.IN_PARTY, DemonRegistration.ON_LOAN):
			await MessageView.send(ctx.channel, CompendiumMsg.already_in_party())
			return

		# Check if player has enough mag to summon.
		cost = costs.summon_cost(demon.rank)
		mag = await currency_queries.get_mag(player_id, server_id)
		if mag < cost:
			await MessageView.send(ctx.channel, CompendiumMsg.summon_cost_not_enough(demon_name, mag, cost))
			return

		# All success. Send a confirmation view with the cost.
		message = CompendiumMsg.confirm_summon_cost(demon_name, cost)
		confirmed = await ConfirmationView.send(ctx, message, player_id)
		if not confirmed:
			return

		# Operations. Take cash, put demon in party and update stats.
		await asyncio.gather(
			currency_queries.update_mag(player_id, server_id, -cost),
			player_demons_queries.set_demon_in_party(player_id, server_id, demon.id),
			player_demons_queries.update_party(player_id, server_id),
		)

		# Final message.
		await MessageView.send(
			ctx.channel,
			CompendiumMsg.summoned_to_party(demon.race, demon.name),
			thumbnail=demon.design_data.profile_img,
			colour=demon.design_data.colour,
		)

	@checks.has_profile()
	@commands.command(**command_kwargs(COMPENDIUM_COMMANDS, "entry"))
	async def entry_command(self, ctx: commands.Context, *, demon_name: str | None) -> None:
		# if demon_name is None:
		# 	await MessageView.send(ctx.channel, CompendiumMsg.no_input_given(COMPENDIUM_COMMANDS["entry"]))
		# 	return

		player_id, server_id = gets.get_player_server_ids(ctx)
		# demon_name = demon_name.title()
		# demon_id = await demon_queries.get_demon_id_by_name(demon_name)
		# reg_status = (
		# 	await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
		# 	if demon_id is not None
		# 	else DemonRegistration.UNREGISTERED
		# )

		# # If not in compendium or the demon at ID doesn't exist, send not in comp.
		# if reg_status == DemonRegistration.UNREGISTERED:
		# 	await MessageView.send(ctx.channel, CompendiumMsg.not_in_comp(demon_name))
		# 	return

		# 1. We want to get 3 entries, one before and one after for loading purposes.
		# 2. Using the DemonData we have, fill in a new view of the demon.
		await DemonEntryBrowser.send(
			ctx.channel,
			player_id,
			server_id,
			# (2, 3, 8, 10, 13, 15, 17, 18, 20),
			(100, 15, 24, 33, 70, 7, 1, 34, 84, 88, 89, 105, 85),
			shown_demon_id=15,
		)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Compendium(bot))
