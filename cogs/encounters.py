import asyncio
import time

from typing import cast

import discord

from discord.ext import commands

from entities.command_data import ENCOUNTERS_COMMANDS, command_kwargs
from entities.demon_data import DemonData
from entities.player_data import ENCOUNTER_WINDOW_HOURS
from helpers import checks, encounter_utils, gets
from queries import demon_queries, player_queries, server_level_queries, server_queries
from views.common_view import MessageView
from views.encounter_view import EncounterViewInitial


class Encounters(commands.Cog):
	"""
	Cog handles standard type demon encounters. Encounter is represented as a layout view with
	options as buttons.
	"""

	def __init__(self, bot: commands.Bot):
		"""Init for the Encounters cog."""
		self.bot = bot

	@checks.is_developer()
	@commands.command(**command_kwargs(ENCOUNTERS_COMMANDS, "test_encounter"))
	async def test_encounter_command(self, ctx: commands.Context, *, name: str | None = None) -> None:
		"""Command to start a test encounter with a random demon."""
		try:
			if not isinstance(ctx.channel, discord.TextChannel):
				raise RuntimeError("ERROR: test_encounter_command | Could not find the channel to send the encounter to.")

			player_id, server_id = gets.get_player_server_ids(ctx)
			d = (
				demon_queries.get_random_demon()
				if name is None
				else demon_queries.get_demon_by_name(player_id, server_id, name)
			)

			if d is None:
				print(f"WARN: Demon {name} was None.")
				return

			await self._start_encounter(ctx.channel, d, 1)
		except Exception as e:
			raise RuntimeError(f"ERROR: encounters.py | test_encounter_command | {e}")

	@checks.in_set_channel()
	@commands.command(**command_kwargs(ENCOUNTERS_COMMANDS, "encounter"))
	async def encounter_demon_command(self, ctx: commands.Context) -> None:
		"""Command to trigger a daily demon encounter."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		player_data = await player_queries.get_player(player_id, server_id)
		set_channel = await server_queries.get_dedicated_channel(server_id)
		send_to_channel = cast(discord.TextChannel, self.bot.get_channel(set_channel) if set_channel else ctx.channel)

		# If its the player's first encounter, send the tutorial one instead.
		if player_data is None:
			await self._start_tutorial_encounter(send_to_channel, player_id, server_id, ctx.author.name)
			return

		# Get the time and the period where the current encounter window started.
		now = int(time.time())
		current_window = encounter_utils.get_current_encounter_window(now)

		# If encounter has already been made in this period, send a message with how long remaining.
		if current_window < player_data.encounter_timer:
			window_seconds = ENCOUNTER_WINDOW_HOURS * 3600
			remaining = (current_window + window_seconds) - now
			hours, remainder = divmod(remaining, 3600)
			minutes, seconds = divmod(remainder, 60)

			view = MessageView(f"Encounter is on cooldown. Try again in **{hours}h**, **{minutes}m** and **{seconds}s**.")
			await send_to_channel.send(view=view)
			return

		# If encounter is available, calculate rank of demon then select a random one from it.
		average_rank = player_data.party_stats.average

		count, server_cap = await asyncio.gather(
			encounter_utils.get_count_for_encounters(server_id),
			server_level_queries.get_rank_cap(server_id),
		)
		demon = await demon_queries.get_demon_by_distribution(player_id, server_id, average_rank, server_cap)

		# Start the encounter.
		await asyncio.gather(
			self._start_encounter(send_to_channel, demon, count),
			player_queries.set_encounter_timer(player_id, server_id, now),
		)

	async def _start_encounter(
		self,
		send_to_channel: discord.TextChannel,
		demon_data: DemonData,
		count: int,
		exclusive_to: int | None = None,
	) -> None:
		"""
		Send an encounter to a channel.

		Args:
		    send_to_channel (discord.TextChannel): Channel to send the encounter to.
			demon_data (DemonData): The demon to send.
			exclusive_to (discord.Member | None): Optional lock encounter to the player.
		"""
		view = EncounterViewInitial(demon_data, count=count, user_exclusive_to=exclusive_to)
		sent = await send_to_channel.send(view=view)
		view.message = sent

	async def _start_tutorial_encounter(
		self,
		send_to_channel: discord.TextChannel,
		player_id: int,
		server_id: int,
		player_name: str,
	) -> None:
		"""Stores new player data into the DB and begins a forced encounter with a Pixie that acts as a tutorial."""

		try:
			if await player_queries.setup_player(player_id, server_id):
				view = MessageView(
					f"-# `> {player_name} has been registered to the DDS-Net! Welcome and enjoy your stay!`"
					"\n\nOnce you're done with your first encounter, you can try another straight away."
					" Explore the `>party` and `>comp` commands too."
					"\n\nYour first encounter will begin now..."
				)
				await send_to_channel.send(view=view)

				tut_demon = "pixie"
				demon = demon_queries.get_demon_by_name(player_id, server_id, tut_demon)

				if demon is None:
					raise RuntimeError(
						f"ERROR: _start_tutorial_encounter | Demon {tut_demon} was not found in the database."
					)

				view = EncounterViewInitial(demon, user_exclusive_to=player_id, tutorial=True)
				await send_to_channel.send(view=view)
		except Exception as e:
			raise RuntimeError(f"ERROR: encounters.py | _start_tutorial_encounter | {e}")


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Encounters(bot))
