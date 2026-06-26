from discord.ext import commands

from entities.command_data import PARTY_COMMANDS, command_kwargs
from entities.player_data import PlayerData
from entities.view_data import Columns, get_args
from helpers import checks, gets
from helpers.costs import party_slot_cost
from helpers.views import ConfirmationView, MessageView, PartyView
from queries import demon_queries, player_demons_queries
from queries.currency_queries import update_mag
from queries.player_queries import get_player, increase_party_slots
from shared_enums import DemonRegistration


class Party(commands.Cog):
	"""Cog for viewing and managing player parties."""

	def __init__(self, bot: commands.Bot):
		"""Init the Party cog with reference to bot instance and database classes."""
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "party"))
	async def party_command(self, ctx: commands.Context, *args: str) -> None:
		"""
		Command to display player's current party.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check party for.
		"""

		player, server = gets.get_player_server(ctx)
		mentioned = None
		columns = list(Columns.PLAYER_DEFAULT)

		if args:
			columns, mentioned = get_args(args, server, columns)

		player = mentioned if mentioned is not None else player

		party_list = await player_demons_queries.check_party(player.id, server.id)
		sd_id = player_demons_queries.get_selected_demon_id(player.id, server.id)
		party_stats = await player_demons_queries.get_party_stats(player.id, server.id)

		view = PartyView(player.name, party_list, columns, selected_demon_id=sd_id, party_stats=party_stats)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "release"))
	async def release_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		"""
		Command to release a demon from the player's party.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to release from the party. The * before it in the arguments
				allows for multi-word demon names.
		"""

		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_name = demon_name.title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)

		if demon_id is None:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Check if demon is in party.
		in_party = await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)

		if in_party != DemonRegistration.IN_PARTY:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(f"Are you sure you want to release **{demon_name}**?", confirmLabel="Yes", denyLabel="No")
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		await player_demons_queries.set_demon_in_party(player_id, server_id, demon_id, set_in_party=False)
		msg = MessageView(
			f"### Good-Bye...\n**{demon_name}** will have a happy life in a faraway forest."
			f"You will never see your **{demon_name}** again."
		)
		await ctx.send(view=msg)

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "increase_party"))
	async def increase_party_command(self, ctx: commands.Context, number: int = 1) -> None:
		player_id, server_id = gets.get_player_server_ids(ctx)
		player_data = await get_player(player_id, server_id)

		if player_data is None:
			raise RuntimeError("ERROR: increase_party_command | Player found but no data retrieved.")

		await self._increase_party_slots_check(ctx, player_data, number)

	async def _increase_party_slots_check(self, ctx, p: PlayerData, number: int) -> None:
		party_cap = p.party_stats.cap
		cost = party_slot_cost(party_cap, number)

		# Check if player has enough, otherwise exit early.
		if p.mag < cost:
			msg = MessageView(f"The cost to increase party slots is **{cost}** MAG. You don't have enough Magnetite!")
			await ctx.send(view=msg)
			return

		# Confirmation window.
		view = ConfirmationView(
			(
				f"Would you like to increase your available party slots by **{number}**?"
				f"\n\nCost: **{cost} MAG**"
				"\n-# Cost increases by **500 MAG** per slot."
			),
			confirmLabel="Yes",
			denyLabel="No",
		)
		result = await ConfirmationView.send_message(view, ctx)
		if result is False or result is None:
			return

		# Increase slots and take cash.
		await increase_party_slots(p.player_id, p.server_id, number)
		update_mag(p.player_id, p.server_id, -cost)

		msg = MessageView(f"Your available party slots increased from **{party_cap}** to **{party_cap + number}**!")
		await ctx.send(view=msg)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Party(bot))
