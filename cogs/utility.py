import asyncio

import discord

from discord.ext import commands

from entities.command_data import UTILITY_COMMANDS, command_kwargs
from entities.demon_data import TOO_WEAK_LEEWAY
from entities.player_data import DAILY_COOLDOWN, ENCOUNTER_WINDOW
from helpers import checks, gets, utils
from helpers.costs import daily_mag
from helpers.messages import UtilityMsgs as Messages
from queries import currency_queries, player_queries, server_level_queries, server_queries
from views.common_view import MessageView


class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "stuff"))
	async def stuff_command(self, ctx: commands.Context) -> None:
		"""Command to view MAG, daily timer, all that jazz."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		player_data, server_data = await asyncio.gather(
			player_queries.get_player(player_id, server_id),
			server_level_queries.get_server_status(server_id),
		)

		if player_data is None:
			raise RuntimeError("Player was not found despite existence check.")

		# Get current time and subtract it from when the player's timer was set.
		time_until_daily = utils.get_time_until(player_data.daily_timer, DAILY_COOLDOWN)
		daily_string = Messages.get_daily_available(time_until_daily)

		# Get the time and the period where the current encounter window started.
		time_until_encounter = utils.get_time_until(player_data.encounter_timer, ENCOUNTER_WINDOW)
		encounter_string = Messages.get_encounter_available(time_until_encounter)

		# Get stats of the player and specific server ones.
		mag = player_data.mag
		stats = player_data.party_stats
		stats_string = Messages.get_encounter_stats(server_data.rank_cap, stats.average, stats.strongest, TOO_WEAK_LEEWAY)

		message = Messages.build_stuff_details(mag, encounter_string, daily_string, stats_string)
		await MessageView.send(ctx.channel, message)

	@checks.has_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "daily"))
	async def daily_command(self, ctx: commands.Context) -> None:
		"""Command to get some free MAG every, however many hours."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		player_data = await player_queries.get_player(player_id, server_id)

		if player_data is None:
			raise RuntimeError("Player was not found despite existence check.")

		time_until = utils.get_time_until(player_data.daily_timer, DAILY_COOLDOWN)

		# If time not up, send how long left.
		if time_until is not None:
			await MessageView.send(ctx.channel, Messages.get_daily_available(time_until))
			return

		add_mag = daily_mag()
		total_mag = player_data.mag + add_mag
		message = Messages.discovered_mag(add_mag, total_mag)

		# Add mag, set timer and send final message.
		await asyncio.gather(
			currency_queries.update_mag(player_id, server_id, add_mag),
			player_queries.set_daily_timer(player_id, server_id),
			MessageView.send(ctx.channel, message),
		)

	@checks.is_developer()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "give_mag"))
	async def give_mag_command(self, ctx: commands.Context, amount: int) -> None:
		"""Add MAG to self for testing."""

		player_id, server_id = gets.get_player_server_ids(ctx)
		await currency_queries.update_mag(player_id, server_id, amount)
		mag = await currency_queries.get_mag(player_id, server_id)
		await MessageView.send(ctx.channel, Messages.discovered_mag(amount, mag))

	@checks.is_admin()
	@checks.has_server_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "set_channel"))
	async def set_channel_command(self, ctx: commands.Context, channel: discord.TextChannel | None) -> None:
		"""Set the dedicated channel for encounters."""

		server_id = gets.get_server(ctx).id

		# Treat command as a check type command if no input.
		if channel is None:
			channel_id = await server_queries.get_dedicated_channel(server_id)

			# Show channel if it has been set.
			if channel_id:
				await MessageView.send(ctx.channel, Messages.show_dedicated_channel(channel_id))
				return

			# Show help otherwise.
			await MessageView.send(ctx.channel, Messages.no_input_given(UTILITY_COMMANDS["set_channel"]))
			return

		# We only want the ID.
		channel_id = channel.id if isinstance(channel, discord.TextChannel) else channel

		# Set channel and send final message.
		await asyncio.gather(
			server_queries.set_dedicated_channel(server_id, channel_id),
			MessageView.send(ctx.channel, Messages.set_dedicated_channel(channel_id)),
		)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Utility(bot))
