import random

import discord

from discord.ext import commands

from entities.command_data import FUSION_COMMANDS, command_kwargs
from entities.demon_data import DemonData, SpecialFusionData
from helpers import checks, costs, gets
from queries import currency_queries, demon_queries, fusion_queries, player_demons_queries
from shared_enums import DemonRegistration, ShopColour
from views.common_view import ConfirmationView, MessageView
from views.shop_view import SpecialFusionView


class Fusion(commands.Cog):
	"""Cog for demon-related commands and functionality."""

	def __init__(self, bot):
		self.bot = bot
		self.players_in_fusion: set[int] = set()

	@checks.has_profile()
	@commands.command(**command_kwargs(FUSION_COMMANDS, "fuse"))
	async def fuse_command(self, ctx: commands.Context, *, input_str: str | None = None) -> None:
		player, server = gets.get_player_server(ctx)

		if player.id in self.players_in_fusion:
			await ctx.send("You're already in the process of fusing...")
			return

		self.players_in_fusion.add(player.id)

		# Using try, finally apparently runs finally even if an unhandled exception occurs.
		try:
			parts = input_str.split(";") if input_str else None
			await self._fuse_demons(ctx, player, server, parts)
		finally:
			self.players_in_fusion.discard(player.id)

	@checks.has_profile()
	@commands.command(**command_kwargs(FUSION_COMMANDS, "special_fusion"))
	async def special_fusion_command(self, ctx: commands.Context) -> None:
		"""Command to view the Rags Shop and trade gems for items."""

		# print("DEBUG: In special_fusion")
		server_id = gets.get_server(ctx).id

		entries = await fusion_queries.get_special_fusion_list(server_id)
		view = SpecialFusionView(entries, self._purchase_callback, colour=ShopColour.SP_FUSION.value)
		await ctx.send(view=view)

	# self.shop_items = database_paths.load_json(database_paths.ITEMS_JSON)
	async def _purchase_callback(self, interaction, fusion_result: SpecialFusionData) -> None:
		"""Callback for when an item purchase button is clicked."""

		player_id = interaction.user.id
		server_id = interaction.guild.id
		demon = fusion_result.demon_data
		ingredients = fusion_result.ingredients

		# Check if demon already exists in party.
		in_party = await player_demons_queries.check_demon_registration(player_id, server_id, demon.id)

		if in_party == DemonRegistration.IN_PARTY:
			msg = MessageView(f"You already have **{demon.name}** in your party...")
			await interaction.response.send_message(view=msg)
			return

		# Check if player has space.
		if not player_demons_queries.get_party_has_space(player_id, server_id):
			msg = MessageView(
				f"Cannot summon **{demon.name}**. Party is full. You can increase capacity using `>increase_party`."
			)
			await interaction.response.send_message(view=msg)
			return

		ing_text = ""

		# CHeck if demon ingredients are in party.
		for i in ingredients:
			in_party = await player_demons_queries.check_demon_registration(player_id, server_id, i.ing_id)

			if in_party != DemonRegistration.IN_PARTY:
				msg = MessageView(f"You do not have a **{i.name}** in your party...")
				await interaction.response.send_message(view=msg)
				return

			ing_text += f"\n-# - {i.race} {i.name}"

		# Send confirmation
		view = ConfirmationView(
			f"In order to summon **{demon.race} {demon.name}**, the following must be sacrificed:"
			f"{ing_text}"
			f"\n\nComplete the ritual?",
			confirmLabel="Summon",
			confirmColour=discord.ButtonStyle.primary,
			image=demon.profile_url,
		)
		result = await ConfirmationView.send_message(view, interaction)

		if result is False or result is None:
			return

		# Remove demons being fused from party.
		for i in ingredients:
			await player_demons_queries.set_demon_in_party(player_id, server_id, i.ing_id, set_in_party=False)

		await player_demons_queries.add_demon_to_compendium(player_id, server_id, demon.id, demon.rank)
		await player_demons_queries.set_demon_in_party(player_id, server_id, demon.id, set_in_party=True)

		# Needs to be a followup.
		msg = MessageView(f"You have successfully summoned **{demon.race} {demon.name}**!", image=demon.profile_url)
		await interaction.followup.send(view=msg)

	async def _fuse_demons(
		self,
		ctx: commands.Context,
		player: discord.Member,
		server: discord.Guild,
		parts: list[str] | None = None,
	):
		if not parts or len(parts) <= 1:
			await ctx.send("Select the demons you wish to fuse by using `>fuse {demon 1}; {demon 2}`.")
			return

		name_1 = parts[0].strip().title()
		name_2 = parts[1].strip().title()

		demon_1 = demon_queries.get_demon_by_name(name_1)
		demon_2 = demon_queries.get_demon_by_name(name_2)

		if not demon_1 or not demon_2:
			await ctx.send("Bad name")
			return

		# Check if in party.
		for i in demon_1.id, demon_2.id:
			if await player_demons_queries.check_demon_registration(player.id, server.id, i) != DemonRegistration.IN_PARTY:
				await ctx.send(f"{i} not in party")
				return

		# Do a different process if fusing with an Element demon.
		if demon_1.race == "Element" or demon_2.race == "Element":
			element, demon = (demon_1, demon_2) if demon_1.race == "Element" else (demon_2, demon_1)
			demon_result = fusion_queries.get_fuse_with_element(demon.race, element.name, original_rank=demon.rank)
		else:
			average_rank = demon_1.rank + demon_2.rank // 2
			demon_result = fusion_queries.get_fused_demon(demon_1.race, demon_2.race, average_rank)

		# Unique message if no demon can be fused.
		if not demon_result or demon_result.id in [demon_1.id, demon_2.id]:
			view = MessageView(f"**{name_1}** + **{name_2}** = **Nothing! So sorry about that champ!**")
			await ctx.send(view=view)
			return

		# Check if the fused demon is already in the player's party.
		if (
			await player_demons_queries.check_demon_registration(player.id, server.id, demon_result.id)
			== DemonRegistration.IN_PARTY
		):
			view = MessageView(
				(
					f"**{demon_1.race} {name_1}** + **{demon_2.race} {name_2}** = "
					f"**{demon_result.race} {demon_result.name}**"
					f"\n\n{demon_result.name} can already be found in your party..."
				),
				demon_result.profile_url,
				demon_result.colour,
			)
			await ctx.send(view=view)
			return

		cost = costs.fusion_cost(demon_result.rank)

		view = MessageView(
			f"**{demon_1.race} {name_1}** + **{demon_2.race} {name_2}** = **{demon_result.race} {demon_result.name}**",
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

		# Fusion Accident code.
		is_fusion_accident = random.random() < 0.01
		if is_fusion_accident:
			demon_result = await self._try_fusion_accident(player.id, server.id, demon_result)

		# Remove demons being fused from party.
		await player_demons_queries.set_demon_in_party(player.id, server.id, demon_1.id, set_in_party=False)
		await player_demons_queries.set_demon_in_party(player.id, server.id, demon_2.id, set_in_party=False)
		currency_queries.update_mag(player.id, server.id, -cost)

		new_demon = await player_demons_queries.add_demon_to_compendium(
			player.id, server.id, demon_result.id, demon_result.rank
		)
		await player_demons_queries.set_demon_in_party(player.id, server.id, demon_result.id, set_in_party=True)

		fuse_complete_text = ""

		if is_fusion_accident:
			fuse_complete_text = "Hmm... It seems an unexpected demon was born... "

		fuse_complete_text += (
			f"\n\n-# **{demon_result.name.capitalize()}**:"
			f"\n-# I'm **{demon_result.race} {demon_result.name}**. Well, it's nice to meet you."
		)
		if new_demon:
			fuse_complete_text += (
				f"\n\n-# `> {demon_result.race} {demon_result.name} has been registered to your compendium.`"
			)

		view = MessageView(
			fuse_complete_text,
			demon_result.profile_url,
			demon_result.colour,
		)
		await ctx.send(view=view)

	async def _try_fusion_accident(self, player_id: int, server_id: int, og_demon: DemonData) -> DemonData:
		accident = demon_queries.get_random_unowned_demon(player_id, server_id, og_demon.rank)

		# Check if demon_result is the same, very rare but don't treat it like an accident in that case.
		return og_demon if og_demon.id == accident.id else accident


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Fusion(bot))
