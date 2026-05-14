from discord.ext import commands

from helpers import checks


class CheckHandler(commands.Cog):
	"""Cog for handling checks that are used across multiple cogs."""

	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@commands.Cog.listener()
	async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
		"""Global error handler for command errors."""
		match error:
			case checks.IsDeveloperCheck():
				# Fail silently.
				pass
			case checks.NotInServerCheck():
				await ctx.reply(str(error), mention_author=False)
			case checks.ProfileSetupCheck():
				await ctx.reply(str(error), mention_author=False)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(CheckHandler(bot))
