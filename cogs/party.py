import asyncio

from discord.ext import commands

from entities.command_data import PARTY_COMMANDS, command_kwargs
from entities.view_data import Columns, get_args
from helpers import checks, gets
from helpers.costs import party_slot_cost
from helpers.messages import PartyMsg
from queries import demon_queries, gem_queries, player_demons_queries
from queries.currency_queries import update_mag
from queries.player_queries import get_player, increase_party_slots
from shared_enums import DemonRegistration
from views.common_view import ConfirmationView, MessageView
from views.table_view import PartyView


class PartyCommands(commands.Cog):
	"""Cog for viewing and managing player parties."""

	def __init__(self, bot: commands.Bot):
		"""Init the Party cog with reference to bot instance and database classes."""
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "party"))
	async def party_command(self, ctx: commands.Context, *args: str) -> None:
		"""Command to display a player's current party."""

		try:
			player, server = gets.get_player_server(ctx)
			mentioned = None
			columns = list(Columns.PLAYER_DEFAULT)

			if args:
				columns, mentioned = get_args(args, server, columns)
			need_gems = Columns.GEMS in columns

			player = mentioned if mentioned is not None else player

			party_entries, party_stats, sd_id = await asyncio.gather(
				player_demons_queries.check_party(player.id, server.id, need_gems),
				player_demons_queries.get_party_stats(player.id, server.id),
				player_demons_queries.get_selected_demon_id(player.id, server.id),
			)

			await PartyView.send(
				ctx.channel,
				party_entries,
				columns,
				player.name,
				party_stats=party_stats,
				selected_demon_id=sd_id,
			)
		except Exception as e:
			raise RuntimeError(f"party_command | {e}")

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "release"))
	async def release_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		"""Command to release a demon from the player's party."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_name = demon_name.title()
		demon_id = await demon_queries.get_demon_id_by_name(demon_name)

		if demon_id is None:
			await MessageView.send(ctx.channel, PartyMsg.not_in_party(demon_name))
			return

		# Check if demon is in party.
		in_party = await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
		if in_party == DemonRegistration.ON_LOAN:
			await MessageView.send(ctx.channel, PartyMsg.currently_on_loan(demon_name))
			return

		if in_party != DemonRegistration.IN_PARTY:
			await MessageView.send(ctx.channel, PartyMsg.not_in_party(demon_name))
			return

		# Send a confirmation view.
		message = PartyMsg.confirm_release(demon_name)
		result = await ConfirmationView.send(ctx, message, player_id, confirm_label="Yes", deny_label="No")
		if result in (False, None):
			return

		# Operations to remove demon from party and update stats.
		asyncio.gather(
			player_demons_queries.set_demon_in_party(player_id, server_id, demon_id, set_in_party=False),
			player_demons_queries.update_party(player_id, server_id, party_add=-1),
		)

		await MessageView.send(ctx.channel, PartyMsg.demon_released(demon_name))

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "increase_party"))
	async def increase_party_command(self, ctx: commands.Context, number: int = 1) -> None:
		try:
			pid, sid = gets.get_player_server_ids(ctx)
			p_data = await get_player(pid, sid)

			if p_data is None:
				raise RuntimeError("Player was not found despite existence check.")

			party_cap = p_data.party_stats.cap
			cost = party_slot_cost(party_cap, number)

			# Check if player has enough MAG.
			if p_data.mag < cost:
				await MessageView.send(ctx.channel, PartyMsg.increase_party_cost_not_enough(cost, p_data.mag))
				return

			# Confirmation window.
			message = PartyMsg.confirm_increase_party(number, cost)
			confirmed = await ConfirmationView.send(ctx, message, p_data.player_id, confirm_label="Yes", deny_label="No")
			if not confirmed:
				return

			# Increase slots and take cash.
			await asyncio.gather(
				increase_party_slots(p_data.player_id, p_data.server_id, number),
				update_mag(p_data.player_id, p_data.server_id, -cost),
			)

			await MessageView.send(ctx.channel, PartyMsg.increased_party_success(party_cap, number))
		except Exception as e:
			raise RuntimeError(f"increase_party_command | {e}")


class LeaderCommands(commands.Cog):
	"""Cog for demon-related commands and functionality."""

	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(PARTY_COMMANDS, "leader"))
	async def leader_command(self, ctx: commands.Context, *, demon_name: str | None) -> None:
		if demon_name:
			await self._select_demon_to_lead(ctx, demon_name)
			return
		await self._check_leader(ctx)

	async def _select_demon_to_lead(self, ctx: commands.Context, demon_name: str) -> None:
		"""Select a demon to lead your party."""
		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_name = demon_name.title()
		demon_id = await demon_queries.get_demon_id_by_name(demon_name)

		# Repeat the same message to avoid giving away whether a demon exists or not.
		if demon_id is None:
			await MessageView.send(ctx.channel, PartyMsg.not_in_party(demon_name))
			return

		# Check if demon is in party first.
		reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
		if reg_status == DemonRegistration.ON_LOAN:
			await MessageView.send(ctx.channel, PartyMsg.currently_on_loan(demon_name))
			return

		if reg_status != DemonRegistration.IN_PARTY:
			await MessageView.send(ctx.channel, PartyMsg.not_in_party(demon_name))
			return

		# Send message and update who is selected.
		dd = await demon_queries.get_design_data(demon_id, player_id, server_id)
		message = PartyMsg.chosen_to_lead(demon_name)
		await asyncio.gather(
			player_demons_queries.set_selected_demon(player_id, server_id, demon_id),
			MessageView.send(ctx.channel, message, thumbnail=dd.profile_img, colour=dd.colour),
		)

	async def _check_leader(self, ctx: commands.Context) -> None:
		"""Check stats of the current leader."""
		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_id = await player_demons_queries.get_selected_demon_id(player_id, server_id)

		# This should never happen.
		if demon_id is None:
			await MessageView.send(ctx.channel, PartyMsg.no_leader())
			return

		demon, mag_mult, gem_progress = await asyncio.gather(
			demon_queries.get_demon_by_id(player_id, server_id, demon_id),
			player_demons_queries.get_demon_mag_mult(player_id, server_id, demon_id),
			gem_queries.get_gem_progress(player_id, server_id, demon_id),
		)

		# Get gems player can get with demon. Needs demon first.
		gems = await gem_queries.get_possible_gems(demon.race)

		await MessageView.send(
			ctx.channel,
			PartyMsg.leader_stats(mag_mult, gems, gem_progress, demon),
			thumbnail=demon.design_data.profile_img,
			colour=demon.design_data.colour,
		)


class Party(PartyCommands, LeaderCommands):
	def __init__(self, bot):
		self.bot = bot


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Party(bot))
