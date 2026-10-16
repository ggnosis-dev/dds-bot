import asyncio

import discord

from discord.ext import commands

from entities import tutorial_data
from entities.command_data import UTILITY_COMMANDS, command_kwargs
from entities.demon_data import TOO_WEAK_LEEWAY
from entities.player_data import DAILY_COOLDOWN, ENCOUNTER_WINDOW
from helpers import checks, gets, utils
from helpers.costs import daily_mag
from helpers.messages import UtilityMsgs as Messages
from queries import currency_queries, demon_queries, player_queries, server_level_queries, server_queries
from views.common_view import MessageView
from views.goal_view import GoalView


class PlayerUtil(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "stuff"))
	async def stuff_command(self, ctx: commands.Context) -> None:
		"""Command to view MAG, daily timer, all that jazz."""

		user_id, server_id = gets.get_user_server_ids(ctx)
		player_data, server_data = await asyncio.gather(
			player_queries.get_player(user_id, server_id),
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

		player_id, server_id = gets.get_user_server_ids(ctx)
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

	@commands.command(**command_kwargs(UTILITY_COMMANDS, "tutorial"))
	async def tutorial_command(self, ctx: commands.Context) -> None:
		"""Tutorial is not blocked by needing a profile."""
		# Build tutorial view using TutorialStep object.
		player_id, server_id = gets.get_user_server_ids(ctx)
		step, task_mask = await player_queries.get_tutorial_progress(player_id, server_id)
		await GoalView.send(ctx.channel, step, task_mask)

	async def process_tutorial_task(
		self, player_id: int, server_id: int, event: tutorial_data.TutorialEvent, channel
	) -> None:
		"""
		Check for tutorial triggers.
		This will only trigger if a COMMAND is run, so no need to worry about junk attempts.
		"""
		# If tutorial is complete, don't do anything else.
		if await player_queries.check_tutorial_complete(player_id, server_id):
			return

		# Get the tutorial step they are on and the task bitmask.
		# Bitmask structured like 010 where 1 indicates task in that position (i.e. task 2) has been completed.
		step_id, task_mask = await player_queries.get_tutorial_progress(player_id, server_id)
		step = tutorial_data.TUTORIAL_STEPS[step_id]
		new_mask = task_mask

		for task_id, task in step.desc_tasks.items():
			# Bit manipulation, takes 1 and slides its bit left by task_id - 1 places.
			# Task 1: 000 << (1 - 1) = 0b001 -> 1
			# Task 2: 000 << (2 - 1) = 0b010 -> 2
			bit = 1 << (task_id - 1)

			# Bitwise AND check to skip if already done.
			# 101 & 010 = 0b000 -> 0 -> falsy
			# 110 & 010 = 0b010 -> 2 -> truthy
			if task_mask & bit:
				continue

			if task.check is not None and await task.check(event):
				# Bitwise OR compare numbers. 0 | 0 = 0
				new_mask = new_mask | bit
				await channel.send(f"COMPLETED {task.name}")

		# Nothing changed.
		if new_mask == task_mask:
			return

		# Essentially, want to get the number of tasks, then minus one bit to get the full mask:
		# (1 << 3) - 1 where 3 is num of tasks.
		# 0b1000 - 0b1 == 8 - 1 == 7 or 0b111
		full_mask = (1 << len(step.desc_tasks)) - 1

		if new_mask == full_mask:
			await step.on_complete(player_id, server_id)
			await channel.send(f"STEP COMPLETED! Reward: {step.reward_text}")
			await player_queries.next_tutorial_step(player_id, server_id)
			return

		await player_queries.set_tutorial_mask(player_id, server_id, new_mask)

	@commands.Cog.listener()
	async def on_command_completion(self, ctx: commands.Context) -> None:
		assert ctx.command is not None, "Run command check should only occur in on_command_completion."

		player_id, server_id = gets.get_user_server_ids(ctx)
		command_args = tutorial_data.get_command_args(ctx)
		event = tutorial_data.TutorialEvent("command", ctx.command.name, player_id, server_id, args=command_args)
		await self.process_tutorial_task(player_id, server_id, event, ctx.channel)

	@commands.Cog.listener()
	async def on_tutorial_trigger(self, source: commands.Context | discord.Interaction, trigger: str) -> None:
		player_id, server_id = gets.get_user_server_ids(source)
		event = tutorial_data.TutorialEvent("trigger", trigger, player_id, server_id)
		await self.process_tutorial_task(player_id, server_id, event, source.channel)


class ServerUtil(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

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


class DevUtil(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.is_developer()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "give_mag"))
	async def give_mag_command(self, ctx: commands.Context, amount: int) -> None:
		"""Add MAG to self for testing."""

		player_id, server_id = gets.get_user_server_ids(ctx)
		await currency_queries.update_mag(player_id, server_id, amount)
		mag = await currency_queries.get_mag(player_id, server_id)
		await MessageView.send(ctx.channel, Messages.discovered_mag(amount, mag))

	@checks.is_developer()
	@commands.command(**command_kwargs(UTILITY_COMMANDS, "update_entry"))
	async def update_entry_command(self, ctx: commands.Context, *, input_str: str | None) -> None:

		parts = utils.split_input_str(input_str, maximum=5, divider="|", do_title=False)
		print(len(parts))

		# Mod 2 being 1 implies we're missing data.
		if len(parts) < 3 or len(parts) % 2 == 0:
			await MessageView.send(ctx.channel, Messages.no_input_given(UTILITY_COMMANDS["update_entry"]))
			return

		demon_name = parts[0]
		data_to_add = {parts[1]: parts[2]}

		if len(parts) > 3:
			data_to_add[parts[3]] = parts[4]

		demon_id = await demon_queries.get_demon_id_by_name(demon_name)
		if demon_id is None:
			await MessageView.send(ctx.channel, Messages.not_in_comp(demon_name))
			return

		success = await demon_queries.insert_entry_data(demon_id, data_to_add)

		if not success:
			await MessageView.send(ctx.channel, Messages.no_input_given(UTILITY_COMMANDS["update_entry"]))
			return

		await MessageView.send(ctx.channel, Messages.updated_demon_entry(demon_name, data_to_add))


class Utility(DevUtil, PlayerUtil, ServerUtil):
	def __init__(self, bot):
		self.bot = bot


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Utility(bot))
