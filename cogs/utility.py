import asyncio
import time

import discord

from discord.ext import commands

from entities.command_data import UTILITY_COMMANDS, command_kwargs
from entities.demon_data import TOO_WEAK_LEEWAY
from entities.player_data import DAILY_COOLDOWN, ENCOUNTER_WINDOW_HOURS
from helpers import checks, gets
from helpers.costs import daily_mag
from helpers.encounter_utils import get_current_encounter_window
from queries import currency_queries, player_queries, server_level_queries, server_queries
from views.common_view import MessageView


class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "stuff"))
	async def stuff_command(self, ctx: commands.Context):
		"""Command to view MAG, daily timer, all that jazz."""

		player_id, server_id = gets.get_player_server_ids(ctx)

		player_data, server_data = await asyncio.gather(
			player_queries.get_player(player_id, server_id),
			server_level_queries.get_server_status(server_id),
		)

		daily_string = "Daily is available!"
		encounter_time_up = "Encounter is available!"
		encounter_string = None
		mag = 0

		if player_data and server_data:
			mag = player_data.mag
			party_stats = player_data.party_stats
			rank_strongest = (
				party_stats.strongest + TOO_WEAK_LEEWAY if party_stats.strongest + TOO_WEAK_LEEWAY < 100 else 100
			)
			rank_cap = server_data.rank_cap

			encounter_string = (
				f"- Encounters can spawn up to **Rank {rank_cap}** (Server Cap)."
				f"\n- Encounters are weighted to **Rank {party_stats.average}** (Your Party Average)."
				f"\n- Encounters under **Rank {rank_strongest}** can be recruited"
				f" (Your Strongest Demon + {str(TOO_WEAK_LEEWAY)})."
			)

			# Get current time and subtract it from when the player's timer was set.
			time_now = int(time.time())
			time_since = time_now - player_data.daily_timer

			# If still time, send a message with how long remaining.
			if time_since < DAILY_COOLDOWN:
				remaining = DAILY_COOLDOWN - time_since
				hours, remainder = divmod(remaining, 3600)
				minutes, seconds = divmod(remainder, 60)

				daily_string = f"Daily available in **{hours}h**, **{minutes}m** and **{seconds}s**."

			# Check for encounter.
			current_window = get_current_encounter_window(time_now)

			# If encounter has already been made in this period, send a message with how long remaining.
			if current_window < player_data.encounter_timer:
				window_seconds = ENCOUNTER_WINDOW_HOURS * 3600
				remaining = (current_window + window_seconds) - time_now
				hours, remainder = divmod(remaining, 3600)
				minutes, seconds = divmod(remainder, 60)

				encounter_time_up = f"Encounter available in **{hours}h**, **{minutes}m** and **{seconds}s**."

		view = MessageView(f"MAG: **{mag}**\n\n{encounter_time_up}\n\n{daily_string}\n\n{encounter_string}")
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "daily"))
	async def daily_command(self, ctx: commands.Context):
		"""Command to get some free MAG every, however many hours."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		player_data = await player_queries.get_player(player_id, server_id)
		daily_string = ""

		if player_data:
			time_now = int(time.time())
			time_since = time_now - player_data.daily_timer

			if time_since < DAILY_COOLDOWN:
				remaining = DAILY_COOLDOWN - time_since
				hours, remainder = divmod(remaining, 3600)
				minutes, seconds = divmod(remainder, 60)

				daily_string = f"Daily available in **{hours}h**, **{minutes}m** and **{seconds}s**."
			else:
				add_mag = daily_mag()
				total_mag = player_data.mag + add_mag
				currency_queries.update_mag(player_id, server_id, add_mag)
				daily_string = f"You've found **+{add_mag}** MAG! Your total is now **{total_mag}** MAG."
				await player_queries.set_daily_timer(player_id, server_id, time_now)

		view = MessageView(f"{daily_string}")
		await ctx.send(view=view)

	@checks.is_developer()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "give_mag"))
	async def give_mag_command(self, ctx: commands.Context, amount: int):
		"""Add MAG to self for testing."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		currency_queries.update_mag(player_id, server_id, amount)
		mag = currency_queries.get_mag(player_id, server_id)

		view = MessageView(f"Added {amount} MAG.\n\nTotal MAG: **{mag}**")
		await ctx.send(view=view)

	@checks.is_admin()
	@checks.has_server_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "set_channel"))
	async def set_channel_command(self, ctx: commands.Context, channel: discord.TextChannel | None):
		"""Set the dedicated channel for encounters."""

		server_id = gets.get_server(ctx).id

		if channel is None:
			channel_id = await server_queries.get_dedicated_channel(server_id)

			if channel_id:
				view = MessageView(
					f"Encounters will only appear in <#{channel_id}>."
					" You can update this by using `>set_channel {channel_name}`."
				)
			else:
				view = MessageView(
					"Encounters can appear anywhere. Use `>set_channel {channel_name}` to set a dedicated channel."
				)

			await ctx.send(view=view)
			return

		# We only want the ID.
		channel_id = channel.id if isinstance(channel, discord.TextChannel) else channel
		success = await server_queries.set_dedicated_channel(server_id, channel_id)

		if success:
			view = MessageView(f"Encounters will now only appear in <#{channel_id}>")
			await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Utility(bot))
