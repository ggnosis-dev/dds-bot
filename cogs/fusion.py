from discord.ext import commands

from helpers import checks, demon_queries, fusion_queries, player_queries
from helpers.views import ConfirmationView, MessageView
from shared_enums import DemonRegistration


class Fusion(commands.Cog):
	"""Cog for demon-related commands and functionality."""

	def __init__(self, bot):
		self.bot = bot
		self.demon_queries = demon_queries.DemonQueries()
		self.fusion_queries = fusion_queries.FusionQueries()
		self.player_db = player_queries.PlayerQueries()

	@checks.has_profile()
	@commands.command(name="fuse", aliases=["f", "fusion"], description="Fuse two demons together to create another.")
	async def fuse_command(self, ctx, *, input_str: str) -> None:
		parts = input_str.split(";")

		if len(parts) <= 1:
			await ctx.send("Select the demons you wish to fuse by using `>fuse {demon 1}; {demon 2}`.")
			return

		name_1 = parts[0].strip().title()
		name_2 = parts[1].strip().title()
		d_id_1 = self.demon_queries.get_demon_id_by_name(name_1)
		d_id_2 = self.demon_queries.get_demon_id_by_name(name_2)
		player = ctx.author
		server = ctx.guild

		if not d_id_1 or not d_id_2:
			await ctx.send("Bad name")
			return

		# Check if in party first.
		for i in d_id_1, d_id_2:
			if await self.player_db.check_demon_registration(player.id, server.id, i) != DemonRegistration.IN_PARTY:
				await ctx.send(f"{i} not in party")
				return

		demon_result = self.fusion_queries.get_fused_demon(d_id_1, d_id_2)

		if not demon_result:
			view = MessageView(f"**{name_1} + {name_2} = Nothing")
			await ctx.send(view=view)
			return

		view = MessageView(
			f"**{name_1}** + **{name_2}** = **{demon_result.name}**", demon_result.profile_url, demon_result.colour
		)
		await ctx.send(view=view)

		# Send a confirmation view.
		view = ConfirmationView("Do you wish to continue with the fusion?")
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Fusion(bot))
