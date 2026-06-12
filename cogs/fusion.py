from discord.ext import commands

from helpers import checks, currency_queries, demon_queries, fusion_queries, player_queries
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

		demon_1 = self.demon_queries.get_demon_by_name(name_1)
		demon_2 = self.demon_queries.get_demon_by_name(name_2)

		player = ctx.author
		server = ctx.guild

		if not demon_1 or not demon_2:
			await ctx.send("Bad name")
			return

		# Check if in party.
		for i in demon_1.id, demon_2.id:
			if await self.player_db.check_demon_registration(player.id, server.id, i) != DemonRegistration.IN_PARTY:
				await ctx.send(f"{i} not in party")
				return

		average_rank = demon_1.rank + demon_2.rank // 2
		demon_result = self.fusion_queries.get_fused_demon(demon_1.race, demon_2.race, average_rank)

		if not demon_result:
			view = MessageView(f"**{name_1} + {name_2} = Nothing")
			await ctx.send(view=view)
			return

		# TODO: Balance these MAG prices around the place.
		cost = int(10000 * (average_rank * 0.01))

		view = MessageView(
			f"**{name_1}** + **{name_2}** = **{demon_result.name}**",
			demon_result.profile_url,
			demon_result.colour,
		)
		await ctx.send(view=view)

		# Check if player has enough mag to summon. Comes after confirmation view as player's may want to just see cost.
		mag = currency_queries.get_mag(player.id, server.id)

		if mag < cost:
			msg = MessageView(
				f"The cost to fuse these demons are **{cost}** MAG. You don't have enough Magnetite to fuse these demons!"
			)
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(f"Fusing these demons together will cost **{cost}** MAG. Do you wish to continue?")
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		currency_queries.update_mag(player.id, server.id, -cost)
		await self.player_db.set_demon_in_party(player.id, server.id, demon_1.id, party_add=False)
		await self.player_db.set_demon_in_party(player.id, server.id, demon_2.id, party_add=False)
		await self.player_db.set_demon_in_party(player.id, server.id, demon_result.id, party_add=True)

		view = MessageView(
			f"You have fused **{demon_result.name}**!",
			demon_result.profile_url,
			demon_result.colour,
		)
		await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Fusion(bot))
