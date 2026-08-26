from discord.ext import commands

from entities.command_data import PROFILE_COMMANDS, command_kwargs
from helpers import checks, gets
from queries import badge_queries


class Profile(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(PROFILE_COMMANDS, "badges"))
	async def badges_command(self, ctx: commands.Context) -> None:
		"""
		Use an item on a demon.

		Args:
			input_str (str): String containing item name and optional demon name, separated by a semicolon delimiter.
				"item_name; demon_name" or just "item_name" to use on selected demon.
		"""

		player_id, _server_id = gets.get_player_server_ids(ctx)
		demon_badges = badge_queries.get_all_demon_badges(player_id)
		show_badges = ""

		for badge in demon_badges:
			show_badges += f"<:{badge.name}:{badge.emote_id}>"

		await ctx.send(show_badges)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Profile(bot))
