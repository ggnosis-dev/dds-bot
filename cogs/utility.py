import time

from discord.ext import commands

from helpers import checks
from helpers.costs import daily_mag
from helpers.views import MessageView
from queries import currency_queries, player_queries

# TODO: Remove this from encounters.py. Needs to be streamlined.
DAILY_COOLDOWN = 43200 * 2
WINDOW_HOURS = 3


class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="stuff", aliases=["st"], description="Check the stuff.")
	async def stuff_check_command(self, ctx):
		"""Command to view MAG, daily timer, all that jazz."""
		player_id = ctx.author.id
		server_id = ctx.guild.id
		player_data = await player_queries.get_player(player_id, server_id)
		daily_string = "Daily is available!"
		encounter_time_up = "Encounter is available!"
		mag = 0

		if player_data:
			mag = player_data.mag

			# Get current time and subtract it from when the player's timer was set.
			time_now = int(time.time())
			time_since = time_now - player_data.daily_timer

			# If still time, send a message with how long remaining.
			if time_since < DAILY_COOLDOWN:
				remaining = DAILY_COOLDOWN - time_since
				hours, remainder = divmod(remaining, 3600)
				minutes, seconds = divmod(remainder, 60)

				daily_string = f"Daily available in **{hours}h**, **{minutes}m** and **{seconds}s**."

			current_window = get_current_encounter_window(time_now)

			# If encounter has already been made in this period, send a message with how long remaining.
			if current_window < player_data.daily_timer:
				window_seconds = WINDOW_HOURS * 3600
				remaining = (current_window + window_seconds) - time_now
				hours, remainder = divmod(remaining, 3600)
				minutes, seconds = divmod(remainder, 60)

				encounter_time_up = f"Encounter available in **{hours}h**, **{minutes}m** and **{seconds}s**."

		view = MessageView(f"{encounter_time_up}\n\n{daily_string}\n\nMAG: **{mag}**")
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(name="daily", aliases=["d"], description="Get some daily MAG.")
	async def daily_mag_command(self, ctx):
		"""Command to view MAG, daily timer, all that jazz."""
		player_id = ctx.author.id
		server_id = ctx.guild.id
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
				daily_string = f"You've found **+{add_mag}**! Your total is now **{total_mag}**."
				await player_queries.set_daily_timer(player_id, server_id, time_now)

		view = MessageView(f"{daily_string}")
		await ctx.send(view=view)

	@checks.is_developer()
	@commands.command(name="give_mag", aliases=["gm"], description="Give the MAG.")
	async def give_mag_command(self, ctx, amount: int):
		"""Command to view MAG, daily timer, all that jazz."""
		player_id = ctx.author.id
		server_id = ctx.guild.id
		currency_queries.update_mag(player_id, server_id, amount)
		mag = currency_queries.get_mag(player_id, server_id)

		view = MessageView(f"Added {amount} MAG.\n\nTotal MAG: **{mag}**")
		await ctx.send(view=view)


def get_current_encounter_window(now: int) -> int:
	"""Get the current encounter window in seconds. Man, this took me way too long."""
	# Convert window hours to seconds.
	window_seconds = WINDOW_HOURS * 3600

	# How many times the window has elapsed since the beginning.
	windows_elapsed = now // window_seconds

	# Take the number of windows elapsed and multiply it by how long a window takes in seconds.
	# We then know which window we're currently in.
	this_window = windows_elapsed * window_seconds

	return this_window


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Utility(bot))
