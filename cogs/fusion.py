import random

import discord

from discord.ext import commands

from entities.command_data import FUSION_COMMANDS, command_kwargs
from entities.demon_data import TOO_WEAK_LEEWAY
from entities.fusion_data import FusionDemonData, SpecialFusionData
from helpers import checks, costs, gets
from queries import currency_queries, demon_queries, fusion_queries, player_demons_queries
from shared_enums import DemonRegistration, EmbedColours, Emotes
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
		player_id, server_id = gets.get_player_server_ids(ctx)

		if player_id in self.players_in_fusion:
			await ctx.send("You're already in the process of fusing...")
			return

		self.players_in_fusion.add(player_id)

		# Using try, finally apparently runs finally even if an unhandled exception occurs.
		try:
			parts = input_str.split(";") if input_str else None
			await self._fuse_demons(ctx, player_id, server_id, parts)
		finally:
			self.players_in_fusion.discard(player_id)

	@checks.has_profile()
	@commands.command(**command_kwargs(FUSION_COMMANDS, "special_fusion"))
	async def special_fusion_command(self, ctx: commands.Context) -> None:
		"""Command to view the Rags Shop and trade gems for items."""

		# print("DEBUG: In special_fusion")
		server_id = gets.get_server(ctx).id

		entries = await fusion_queries.get_special_fusion_list(server_id)
		view = SpecialFusionView(entries, self._purchase_callback, colour=EmbedColours.SP_FUSION.value)
		await ctx.send(view=view)

	# self.shop_items = database_paths.load_json(database_paths.ITEMS_JSON)
	async def _purchase_callback(self, interaction, fusion_result: SpecialFusionData) -> None:
		"""Callback for when an item purchase button is clicked."""

		player_id = interaction.user.id
		server_id = interaction.guild.id
		demon = fusion_result.fusion_demon_data
		ingredients = fusion_result.ingredients

		party_stats = await player_demons_queries.get_party_stats(player_id, server_id)
		if demon.rank > party_stats.strongest + TOO_WEAK_LEEWAY:
			view = MessageView(
				(
					f"\nBut you are too weak to control **{demon.race} {demon.name}**..."
					f"\n\n-# You can control up to {party_stats.strongest + 3} (Your strongest demon's rank + 3)."
				),
				colour=EmbedColours.SP_FUSION.value,
			)
			await interaction.response.send_message(view=view)
			return

		# Check if demon already exists in party.
		in_party = await player_demons_queries.check_demon_registration(player_id, server_id, demon.id)
		if in_party == DemonRegistration.IN_PARTY or in_party == DemonRegistration.ON_LOAN:
			msg = MessageView(
				f"You already have **{demon.name}** in your party...",
				colour=EmbedColours.SP_FUSION.value,
			)
			await interaction.response.send_message(view=msg)
			return

		ing_text = ""

		# CHeck if demon ingredients are in party.
		for i in ingredients:
			ing_in_party = await player_demons_queries.check_demon_registration(player_id, server_id, i.ing_id)

			if ing_in_party == DemonRegistration.ON_LOAN:
				msg = MessageView(
					f"**{i.race} {i.name}** is currently being loaned to the Server Compendium and can't be fused...",
					colour=EmbedColours.SP_FUSION.value,
				)
				await interaction.response.send_message(view=msg)
				return

			if ing_in_party != DemonRegistration.IN_PARTY:
				msg = MessageView(
					f"You do not have a **{i.race} {i.name}** in your party...",
					colour=EmbedColours.SP_FUSION.value,
				)
				await interaction.response.send_message(view=msg)
				return

			ing_text += f"\n-# - {i.race} {i.name}"

		dd = await demon_queries.get_design_data(demon.id)

		# Send confirmation
		view = ConfirmationView(
			f"In order to summon **{demon.race} {demon.name}**, the following must be sacrificed:"
			f"{ing_text}"
			f"\n\nComplete the ritual?",
			exclusive_to=player_id,
			confirm_label="Summon",
			confirm_colour=discord.ButtonStyle.primary,
			thumbnail=dd.profile_img,
			colour=EmbedColours.SP_FUSION.value,
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
		msg = MessageView(
			f"You have successfully summoned **{demon.race} {demon.name}**!",
			thumbnail=dd.profile_img,
			colour=EmbedColours.SP_FUSION.value,
		)
		await interaction.followup.send(view=msg)

	async def _fuse_demons(
		self,
		ctx: commands.Context,
		player_id: int,
		server_id: int,
		parts: list[str] | None = None,
	):
		# Check parts are valid.
		if not parts or len(parts) <= 1:
			view = MessageView(
				"Select the demons you wish to fuse by using `>fuse {demon 1}; {demon 2}`.",
				colour=EmbedColours.SP_FUSION.value,
			)
			await ctx.send(view=view)
			return

		name_1 = parts[0].strip().title()
		name_2 = parts[1].strip().title()

		demon_1 = demon_queries.get_demon_by_name(player_id, server_id, name_1)
		demon_2 = demon_queries.get_demon_by_name(player_id, server_id, name_2)

		# If the demon doesn't exist at all.
		if not demon_1 or not demon_2:
			view = MessageView(
				"The demons entered for fusion could not be found. You may be yet to register them to your Compendium.",
				colour=EmbedColours.SP_FUSION.value,
			)
			await ctx.send(view=view)
			return

		# Check if in party.
		for d in demon_1, demon_2:
			registration_status = await player_demons_queries.check_demon_registration(player_id, server_id, d.id)
			view = None

			match registration_status:
				case DemonRegistration.UNREGISTERED:
					view = MessageView(
						"The demons entered for fusion could not be found."
						" You may be yet to register them to your Compendium.",
						colour=EmbedColours.SP_FUSION.value,
					)

				case DemonRegistration.IN_COMP:
					view = MessageView(
						f"**{d.race} {d.name}** is not in your party.",
						colour=EmbedColours.SP_FUSION.value,
					)

				case DemonRegistration.ON_LOAN:
					view = MessageView(
						f"**{d.race} {d.name}** is currently being loaned to the Server Compendium and can't be fused...",
						colour=EmbedColours.SP_FUSION.value,
					)

			if view is not None:
				await ctx.send(view=view)
				return

			leader_id = await player_demons_queries.get_selected_demon_id(player_id, server_id)

			if d.id == leader_id:
				view = MessageView(
					f"**{d.race} {d.name}** is currently set as your leader."
					" Use `>select {demon}` to change your leader before fusing.",
					colour=EmbedColours.SP_FUSION.value,
				)
				await ctx.send(view=view)
				return

		# Do a different process if fusing with an Element demon.
		if demon_1.race == "Element" or demon_2.race == "Element":
			element, demon = (demon_1, demon_2) if demon_1.race == "Element" else (demon_2, demon_1)
			demon_result = fusion_queries.get_fuse_with_element(
				demon.race,
				element.name,
				original_rank=demon.rank,
			)
		else:
			# Get the average INITIAL rank of the two demons.
			average_rank = demon_1.rank + demon_2.rank // 2
			demon_result = fusion_queries.get_fused_demon(demon_1.race, demon_2.race, average_rank)

		# Unique message if no demon can be fused.
		if not demon_result or demon_result.id in [demon_1.id, demon_2.id]:
			view = MessageView(
				f"**{name_1}** + **{name_2}** = **Nothing! So sorry about that champ!**",
				colour=EmbedColours.SP_FUSION.value,
			)
			await ctx.send(view=view)
			return

		result_design_data = await demon_queries.get_design_data(demon_result.id)

		# Check if the fused demon is already in the player's party.
		result_reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, demon_result.id)
		if result_reg_status == DemonRegistration.IN_PARTY:
			view = MessageView(
				(
					f"**{demon_1.race} {demon_1.name}** ({demon_1.rank})"
					f" + **{demon_2.race} {demon_2.name}** ({demon_2.rank}) ="
					f"\n### {demon_result.race} {demon_result.name} ({demon_result.rank})"
					f"\n{Emotes.BLANK.value}"
					f"\nBut {demon_result.name} can already be found in your party..."
				),
				result_design_data.profile_img,
				EmbedColours.SP_FUSION.value,
			)
			await ctx.send(view=view)
			return

		# If player's strongest demon is less than the result's rank + 3, do not let them fuse it.
		party_stats = await player_demons_queries.get_party_stats(player_id, server_id)
		if demon_result.rank > party_stats.strongest + TOO_WEAK_LEEWAY:
			view = MessageView(
				(
					f"**{demon_1.race} {demon_1.name}** ({demon_1.rank})"
					f" + **{demon_2.race} {demon_2.name}** ({demon_2.rank}) ="
					f"\n### {demon_result.race} {demon_result.name} ({demon_result.rank})"
					f"\n{Emotes.BLANK.value}"
					"\nBut you are too weak to control it..."
					f"\n\n-# You can control up to {party_stats.strongest + 3} (Your strongest demon's rank + 3)."
				),
				result_design_data.profile_img,
				EmbedColours.SP_FUSION.value,
			)
			await ctx.send(view=view)
			return

		cost = costs.fusion_cost(demon_result.rank)

		view = MessageView(
			(
				f"**{demon_1.race} {demon_1.name}** ({demon_1.rank})"
				f" + **{demon_2.race} {demon_2.name}** ({demon_2.rank}) ="
				f"\n### {demon_result.race} {demon_result.name} ({demon_result.rank})"
			),
			result_design_data.profile_img,
			EmbedColours.SP_FUSION.value,
		)
		await ctx.send(view=view)

		# Check if player has enough mag to summon. Comes after confirmation view as player's may want to just see cost.
		mag = currency_queries.get_mag(player_id, server_id)

		if mag < cost:
			msg = MessageView(
				f"The cost to fuse these demons are **{cost}** MAG. You don't have enough Magnetite to fuse these demons!",
				colour=EmbedColours.SP_FUSION.value,
			)
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(
			f"Fusing these demons together will cost **{cost}** MAG. Do you wish to continue?",
			player_id,
			colour=EmbedColours.SP_FUSION.value,
		)
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		# Fusion Accident code.
		is_fusion_accident = random.random() < 0.01
		if is_fusion_accident:
			demon_result = await self._try_fusion_accident(player_id, server_id, demon_result)

		# Remove demons being fused from party.
		await player_demons_queries.set_demon_in_party(player_id, server_id, demon_1.id, set_in_party=False)
		await player_demons_queries.set_demon_in_party(player_id, server_id, demon_2.id, set_in_party=False)
		currency_queries.update_mag(player_id, server_id, -cost)

		new_demon = await player_demons_queries.add_demon_to_compendium(
			player_id, server_id, demon_result.id, demon_result.rank
		)
		await player_demons_queries.set_demon_in_party(player_id, server_id, demon_result.id, set_in_party=True)

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
			result_design_data.profile_img,
			EmbedColours.SP_FUSION.value,
		)
		await ctx.send(view=view)

	async def _try_fusion_accident(self, player_id: int, server_id: int, og_demon: FusionDemonData) -> FusionDemonData:
		accident = fusion_queries.get_random_unowned_demon(player_id, server_id, og_demon.rank)

		# Check if demon_result is the same, very rare but don't treat it like an accident in that case.
		return og_demon if og_demon.id == accident.id else accident


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Fusion(bot))
