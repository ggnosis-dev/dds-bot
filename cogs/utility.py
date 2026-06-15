import time

from discord.ext import commands

from helpers import checks
from helpers.views import MessageView
from queries import currency_queries, player_queries

# TODO: Remove this from encounters.py. Needs to be streamlined.
DAILY_COOLDOWN = 43200


class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(name="stuff", aliases=["st"], description="Check the stuff.")
	async def stuff_check_command(self, ctx):
		"""Command to view MAG, daily timer, all that jazz."""
		player_id = ctx.author.id
		server_id = ctx.guild.id
		player_data = await player_queries.get_player(player_id, server_id)
		daily_string = "Daily is available!"
		mag = 0
		time_since = 0

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

		view = MessageView(f"{daily_string}\n\nMAG: **{mag}**")
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


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Utility(bot))
