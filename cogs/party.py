import asyncio
import re

from discord.ext import commands

from entities.command_data import DEMONS_COMMANDS, PARTY_COMMANDS, command_kwargs
from entities.demon_data import GREETING_LENGTH
from entities.player_data import PlayerData
from entities.view_data import Columns, get_args
from helpers import checks, gets
from helpers.costs import party_slot_cost
from helpers.format_utils import format_greeting, sanitise_greeting
from queries import demon_queries, gem_queries, player_demons_queries
from queries.currency_queries import update_mag
from queries.player_queries import get_player, increase_party_slots
from shared_enums import DemonRegistration, Emotes, Unicode
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
		"""
		Command to display player's current party.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check party for.
		"""

		try:
			player, server = gets.get_player_server(ctx)
			mentioned = None
			columns = list(Columns.PLAYER_DEFAULT)

			if args:
				columns, mentioned = get_args(args, server, columns)

			player = mentioned if mentioned is not None else player

			need_gems = Columns.GEMS in columns

			party_list, party_stats, sd_id = await asyncio.gather(
				player_demons_queries.check_party(player.id, server.id, need_gems),
				player_demons_queries.get_party_stats(player.id, server.id),
				player_demons_queries.get_selected_demon_id(player.id, server.id),
			)

			view = PartyView(player.name, party_list, columns, selected_demon_id=sd_id, party_stats=party_stats)
			await ctx.send(view=view)
		except Exception as e:
			print(e)
			raise RuntimeError(f"ERROR: party.py | party_command | {e}")

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

		if in_party == DemonRegistration.ON_LOAN:
			msg = MessageView(
				f"**{demon_name}** is currently being loaned to the Server Compendium and can't be released..."
			)
			await ctx.send(view=msg)
			return

		if in_party != DemonRegistration.IN_PARTY:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(
			f"Are you sure you want to release **{demon_name}**?",
			exclusive_to=player_id,
			confirm_label="Yes",
			deny_label="No",
		)
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
		try:
			player_id, server_id = gets.get_player_server_ids(ctx)
			player_data = await get_player(player_id, server_id)

			if player_data is None:
				raise RuntimeError("ERROR: increase_party_command | Player found but no data retrieved.")

			await self._increase_party_slots_check(ctx, player_data, number)
		except Exception as e:
			raise RuntimeError(f"ERROR: party.py | increase_party_command | {e}")

	async def _increase_party_slots_check(self, ctx: commands.Context, p: PlayerData, number: int) -> None:

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
			p.player_id,
			confirm_label="Yes",
			deny_label="No",
		)
		result = await ConfirmationView.send_message(view, ctx)
		if result is False or result is None:
			return

		# Increase slots and take cash.
		await increase_party_slots(p.player_id, p.server_id, number)
		update_mag(p.player_id, p.server_id, -cost)

		msg = MessageView(f"Your available party slots increased from **{party_cap}** to **{party_cap + number}**!")
		await ctx.send(view=msg)


class LeaderCommands(commands.Cog):
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

		registration_status = await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)

		match registration_status:
			case DemonRegistration.ON_LOAN:
				view = MessageView(
					f"**{demon_name}** is currently being loaned to the Server Compendium and can't be selected..."
				)

			case DemonRegistration.IN_COMP | DemonRegistration.UNREGISTERED:
				view = MessageView(f"**{demon_name}** is not in your party...")

			case _:
				dd = await demon_queries.get_design_data(demon_id, player_id, server_id)
				view = MessageView(
					f"**{demon_name}** has been selected to lead your party!", thumbnail=dd.profile_img, colour=dd.colour
				)

		player_demons_queries.set_selected_demon(player_id, server_id, demon_id)
		await ctx.send(view=view)
		return

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "leader"))
	async def leader_command(self, ctx: commands.Context) -> None:
		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_id = await player_demons_queries.get_selected_demon_id(player_id, server_id)

		# This should never happen.
		if demon_id is None:
			await ctx.send("There is currently no demon leading your party. Select one using `>select {demon}`.")
			return

		d = demon_queries.get_demon_by_id(player_id, server_id, demon_id)

		if d is None:
			raise RuntimeError("leader_command | ID was found but DemonData was not.")

		# Get gem progress.
		gem_progress = round(gem_queries.get_gem_progress(player_id, server_id, d.id) / 10)
		progress_bar = f"{Unicode.FILLED_CIRCLE.value} " * gem_progress + f"{Unicode.UNFILLED_CIRCLE.value} " * (
			10 - gem_progress
		)

		# Get gems player can get with demon.
		gems = gem_queries.get_possible_gems(d.race)
		gem_text = " & ".join(gems).title()

		# Get multiplier.
		mag_mult = player_demons_queries.get_demon_mag_mult(player_id, server_id, demon_id)

		view = MessageView(
			(
				f"**{d.race} {d.name}** is currently leading your party."
				f"\n\n-# **Rank:** {d.rank}"
				f"\n-# **Level:** {d.dupes}{Emotes.GEM.value}"
				f"\n-# **MAG Mult:** +{mag_mult}x"
				f"\n-# **Hunting:** {gem_text}"
				f"\n-# **Progress:**\n{progress_bar}"
			),
			d.design_data.profile_img,
			d.design_data.colour,
		)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "demon_colour"))
	async def demon_colour_command(self, ctx: commands.Context, *, input_str: str) -> None:

		player_id, server_id = gets.get_player_server_ids(ctx)
		parts = input_str.split(";")
		demon_name = parts[0].strip().title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)
		reg = (
			await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
			if demon_id is not None
			else DemonRegistration.UNREGISTERED
		)

		# Check if demon is valid. If it is, still check registration as to not reveal demons player haven't seen yet.
		if demon_id is None or reg == DemonRegistration.UNREGISTERED:
			msg = MessageView(f"A **{demon_name}** was not found in your COMP...")
			await ctx.send(view=msg)
			return

		# Anything that returns implies the player has access to customising.
		old_colour = await player_demons_queries.get_custom_colour_on_demon(player_id, server_id, demon_id)

		if old_colour is None:
			msg = MessageView(f"You do not have the ability to customise the embed colour for **{demon_name}** yet.")
			await ctx.send(view=msg)
			return

		# Set to 0 (returns to DEFAULT) if no second part was provided.
		hex_string = parts[1].strip() if len(parts) > 1 else None
		new_colour = 0

		if hex_string is not None:
			# Matches either 3 or 6 valid HEX values. Doesn't care about the #.
			match = re.search(r"^#?([0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)", hex_string)
			if match:
				new_colour = int(match.group(1), 16)

		await player_demons_queries.set_custom_colour_on_demon(player_id, server_id, demon_id, new_colour)
		updated_string = f"updated to **#{new_colour:06X}**" if new_colour != 0 else "reverted to its **DEFAULT**"
		msg = MessageView(
			f"**{demon_name}**'s embed colour has been {updated_string}.",
			colour=new_colour,
		)
		await ctx.send(view=msg)

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "set_greeting"))
	async def set_greeting_command(self, ctx: commands.Context, *, input_str: str) -> None:
		player_id, server_id = gets.get_player_server_ids(ctx)
		parts = input_str.split(";")
		demon_name = parts[0].strip().title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)
		reg = (
			await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
			if demon_id is not None
			else DemonRegistration.UNREGISTERED
		)

		# Check if demon is valid. If it is, still check registration as to not reveal demons player haven't seen yet.
		if demon_id is None or reg == DemonRegistration.UNREGISTERED:
			msg = MessageView(f"A **{demon_name}** was not found in your COMP...")
			await ctx.send(view=msg)
			return

		# Anything past here implies the player has access to customising.
		old_greeting = await player_demons_queries.get_custom_greeting_on_demon(player_id, server_id, demon_id)
		if old_greeting is None:
			msg = MessageView(f"You do not have the ability to customise the greeting for **{demon_name}** yet.")
			await ctx.send(view=msg)
			return

		greeting_string = parts[1].strip() if len(parts) > 1 else None

		# No greeting given, reset to default.
		if greeting_string is None:
			await player_demons_queries.set_custom_greeting_on_demon(player_id, server_id, demon_id)
			msg = MessageView(
				f"**{demon_name}**'s greeting has been reverted to its **DEFAULT**.",
			)
			await ctx.send(view=msg)
			return

		# [r]/[R] and [d]/[D] are required so player's can still see what it is.
		if "[r]" not in greeting_string.lower() or "[d]" not in greeting_string.lower():
			msg = MessageView(
				"Your greeting must include both `[r]`/`[R]` for race name and `[d]`/`[D]` for demon name.",
			)
			await ctx.send(view=msg)
			return

		# Sanitise the message to make sure it's under the character limit and doesn't have evil things in it.
		sanitised_greeting = sanitise_greeting(greeting_string)
		if sanitised_greeting is None:
			msg = MessageView(
				f"Either your greeting is over {GREETING_LENGTH} characters in length, or you're trying to be cheeky.",
			)
			await ctx.send(view=msg)
			return

		# Do not format the string before saving it, otherwise it can never be updated in encounters.
		await player_demons_queries.set_custom_greeting_on_demon(player_id, server_id, demon_id, sanitised_greeting)

		# Format here so the player can view an example instantly.
		demon = demon_queries.get_demon_by_id(player_id, server_id, demon_id)
		formatted_greeting = format_greeting(greeting_string, demon)
		msg = MessageView(
			f'**{demon_name}**\'s greeting has been updated to "{formatted_greeting}".',
			colour=demon.design_data.colour,
		)
		await ctx.send(view=msg)
		return


class Party(PartyCommands, LeaderCommands):
	def __init__(self, bot):
		self.bot = bot


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Party(bot))
