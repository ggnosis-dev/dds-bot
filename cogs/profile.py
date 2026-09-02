from discord.ext import commands

from entities.command_data import PROFILE_COMMANDS, command_kwargs
from helpers import checks, gets
from helpers.messages import ProfileMsg
from queries import badge_queries


class Profile(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(PROFILE_COMMANDS, "badges"))
	async def badges_command(self, ctx: commands.Context) -> None:
		"""Show obtained badges."""

		player_id, _server_id = gets.get_player_server_ids(ctx)
		badges = await badge_queries.get_all_demon_badges(player_id)
		message = ProfileMsg.show_badges(badges) if len(badges) >= 0 else ProfileMsg.no_badges()
		await ctx.send(message)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Profile(bot))
