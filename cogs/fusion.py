import asyncio
import random

import discord

from discord.ext import commands

from entities.command_data import FUSION_COMMANDS, command_kwargs
from entities.demon_data import TOO_WEAK_LEEWAY, DemonData
from entities.fusion_data import FUSION_ACCIDENT_CHANCE, SpecialFusionShopData
from helpers import checks, costs, encounter_utils, gets, utils
from helpers.messages import FusionMsg
from queries import currency_queries, demon_queries, fusion_queries, player_demons_queries
from shared_enums import DemonRegistration, EmbedColours
from views.common_view import ConfirmationView, MessageView
from views.shop_view import SpecialFusionView


class Fusion(commands.Cog):
	"""Cog for demon-related commands and functionality."""

	def __init__(self, bot):
		self.bot = bot
		self.players_in_fusion: set[int] = set()
		self.col = EmbedColours.SP_FUSION.value

	@checks.has_profile()
	@commands.command(**command_kwargs(FUSION_COMMANDS, "fuse"))
	async def fuse_command(self, ctx: commands.Context, *, input_str: str | None) -> None:

		# Reminder first, then check for input lacking.
		player_id, server_id = gets.get_player_server_ids(ctx)
		if player_id in self.players_in_fusion:
			await MessageView.send(ctx.channel, FusionMsg.already_in_fusion())
			return
		self.players_in_fusion.add(player_id)

		# Using try, finally apparently runs finally even if an unhandled exception occurs.
		try:
			# Break into parts, return help message if invalid.
			parts = utils.split_input_str(input_str, maximum=2)
			if len(parts) < 2:
				await MessageView.send(ctx.channel, FusionMsg.no_input_given(FUSION_COMMANDS["fuse"]), colour=self.col)
				return

			await self._fuse_demons(ctx, player_id, server_id, parts)
		finally:
			self.players_in_fusion.discard(player_id)

	async def _fuse_demons(
		self,
		ctx: commands.Context,
		player_id: int,
		server_id: int,
		names: tuple[str, ...],
	) -> None:
		demons = []

		for n in names:
			d = await demon_queries.get_demon_by_name(player_id, server_id, n)

			# Demon doesn't exist. Don't want to be specific to not give away unfound demons.
			if d is None:
				await MessageView.send(ctx.channel, FusionMsg.not_in_party(n), colour=self.col)
				return

			# Check if each demon is summoned to the party.
			reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, d.id)
			if reg_status == DemonRegistration.ON_LOAN:
				await MessageView.send(ctx.channel, FusionMsg.currently_on_loan(n), colour=self.col)
				return

			if reg_status == DemonRegistration.LEADER:
				await MessageView.send(ctx.channel, FusionMsg.currently_leader(n), colour=self.col)
				return

			if reg_status != DemonRegistration.IN_PARTY:
				await MessageView.send(ctx.channel, FusionMsg.not_in_party(n), colour=self.col)
				return

			demons.append(d)

		d1, d2 = demons

		# Do a different process if fusing with an Element demon.
		if d1.race == "Element" or d2.race == "Element":
			element, demon = (d1, d2) if d1.race == "Element" else (d2, d1)
			demon_result = await fusion_queries.get_fuse_with_element(
				player_id, server_id, demon.race, element.name, demon.rank
			)
		else:
			# Get the average INITIAL rank of the two demons.
			average_rank = (d1.rank + d2.rank) // 2
			demon_result = await fusion_queries.get_fused_demon(player_id, server_id, d1.race, d2.race, average_rank)

		# Unique message if demons can't be fused.
		if demon_result is None:
			await MessageView.send(ctx.channel, FusionMsg.cant_fuse(demons), colour=self.col)
			return

		# Get design data and the calculation response.
		dd = await demon_queries.get_design_data(demon_result.id)
		message = FusionMsg.fusion_response(demons, demon_result)

		# If player's strongest demon is less than the result's rank + 3, do not let them fuse it.
		party_stats = await player_demons_queries.get_party_stats(player_id, server_id)
		if demon_result.rank > party_stats.strongest + TOO_WEAK_LEEWAY:
			message += FusionMsg.fusion_too_weak(party_stats.strongest, TOO_WEAK_LEEWAY)
			await MessageView.send(ctx.channel, message, thumbnail=dd.profile_img, colour=self.col)
			return

		cost = costs.fusion_cost(demon_result.rank)

		# Check if demon is already summoned and warn that fusing will only add to its level.
		result_reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, demon_result.id)
		is_summoned = result_reg_status in {DemonRegistration.IN_PARTY, DemonRegistration.ON_LOAN, DemonRegistration.LEADER}
		if is_summoned:
			# Append warning about demon already being in party.
			message += FusionMsg.fusion_already_in_party(demon_result)

		await MessageView.send(
			ctx.channel,
			message,
			thumbnail=dd.profile_img,
			colour=self.col,
		)

		# Check if player has enough mag to summon. Comes after confirmation view as player's may want to just see cost.
		mag = await currency_queries.get_mag(player_id, server_id)
		if mag < cost:
			message = FusionMsg.fusion_not_enough_mag(cost, mag)
			await MessageView.send(ctx.channel, message, colour=self.col)
			return

		# Send a confirmation view.
		confirmed = await ConfirmationView.send(ctx, FusionMsg.confirm_fusion(cost), player_id, colour=self.col)
		if not confirmed:
			return

		# COMMENCE FUSION.
		new_to_comp = False
		dupe_message = None
		is_fusion_accident = random.random() < FUSION_ACCIDENT_CHANCE

		# Try fusion accident.
		if is_fusion_accident:
			demon_result = await self._try_fusion_accident(player_id, server_id, demon_result, demon_result.rank)

		# Remove demons being fused from party.
		await asyncio.gather(
			player_demons_queries.set_demon_in_party(player_id, server_id, d1.id, set_in_party=False),
			player_demons_queries.set_demon_in_party(player_id, server_id, d2.id, set_in_party=False),
			player_demons_queries.update_party(player_id, server_id, party_add=-2),
			currency_queries.update_mag(player_id, server_id, -cost),
		)

		# Try applying dupe level.
		if is_summoned:
			dupe_message = await encounter_utils.grant_dupe_reward(player_id, server_id, demon_result)

			# Send dupe message if it exists.
			if dupe_message is not None:
				await MessageView.send(
					ctx.channel,
					FusionMsg.dupe_level_up(player_id, demon_result, dupe_message),
					thumbnail=dd.profile_img,
					colour=dd.colour,
				)

		# Unregistered or in Compendium.
		else:
			# Check if it's a brand new demon.
			new_to_comp = await player_demons_queries.add_demon_to_compendium(
				player_id, server_id, demon_result.id, demon_result.rank
			)

			# Set it in party, update party count.
			await asyncio.gather(
				player_demons_queries.set_demon_in_party(player_id, server_id, demon_result.id, set_in_party=True),
				player_demons_queries.update_party(player_id, server_id),
			)

		# Send final message.
		await MessageView.send(
			ctx.channel,
			FusionMsg.fusion_completed(demon_result.race, demon_result.name, is_fusion_accident, new_to_comp),
			thumbnail=dd.profile_img,
			colour=dd.colour,
		)

	async def _try_fusion_accident(self, player_id: int, server_id: int, og_demon: DemonData, rank: int) -> DemonData:
		accident = await fusion_queries.get_random_unowned_demon(player_id, server_id, rank)

		# Check if demon_result is the same, very rare but don't treat it like an accident in that case.
		return og_demon if accident is None or og_demon.id == accident.id else accident

	@checks.has_profile()
	@commands.command(**command_kwargs(FUSION_COMMANDS, "special_fusion"))
	async def special_fusion_command(self, ctx: commands.Context) -> None:
		"""Command to view the Rags Shop and trade gems for items."""
		server_id = gets.get_server(ctx).id
		entries = await fusion_queries.get_special_fusion_list(server_id)
		await SpecialFusionView.send(ctx.channel, entries, self._sp_fusion_purchase_callback, colour=self.col)

	async def _sp_fusion_purchase_callback(self, interaction, fusion_result: SpecialFusionShopData) -> None:
		"""Callback for when an item purchase button is clicked."""

		player_id = interaction.user.id
		server_id = interaction.guild.id
		ingredients = fusion_result.ingredients
		fused_demon = await demon_queries.get_demon_by_id(player_id, server_id, fusion_result.demon_id)

		# Check if strong enough to summon it.
		party_stats = await player_demons_queries.get_party_stats(player_id, server_id)
		if fused_demon.rank > party_stats.strongest + TOO_WEAK_LEEWAY:
			message = FusionMsg.fusion_too_weak(party_stats.strongest, TOO_WEAK_LEEWAY)
			await MessageView.reply(
				interaction,
				message,
				colour=self.col,
				ephemeral=True,
			)
			return

		# CHeck if demon ingredients are in party.
		for i in ingredients:
			# Check if each demon is summoned to the party.
			reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, i.ing_id)
			if reg_status == DemonRegistration.ON_LOAN:
				await MessageView.reply(interaction, FusionMsg.currently_on_loan(i.name), colour=self.col, ephemeral=True)
				return

			if reg_status == DemonRegistration.LEADER:
				await MessageView.reply(interaction, FusionMsg.currently_leader(i.name), colour=self.col, ephemeral=True)
				return

			if reg_status != DemonRegistration.IN_PARTY:
				await MessageView.reply(interaction, FusionMsg.not_in_party(i.name), colour=self.col, ephemeral=True)
				return

		# Len of ingredients minus 1 for the new demon.
		party_num_to_remove = -(len(ingredients) - 1)
		dd = await demon_queries.get_design_data(fused_demon.id)

		# Start building the confirmation message.
		message = FusionMsg.confirm_special_fusion(fused_demon.race, fused_demon.name, ingredients)

		# Check if demon is already summoned and warn that fusing will only add to its level.
		fused_reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, fused_demon.id)
		is_summoned = fused_reg_status in {DemonRegistration.IN_PARTY, DemonRegistration.ON_LOAN, DemonRegistration.LEADER}
		if is_summoned:
			# Update party number as we are no longer adding a new demon.
			party_num_to_remove = -(len(ingredients))

			# Append warning message about demon already being in party.
			message += FusionMsg.fusion_already_in_party(fused_demon)

		# Send confirmation.
		confirmed = await ConfirmationView.reply(
			interaction,
			message,
			player_id,
			confirm_label="Summon",
			confirm_colour=discord.ButtonStyle.primary,
			thumbnail=dd.profile_img,
			colour=self.col,
		)
		if not confirmed:
			return

		# Remove demons being fused from party.
		tasks = []
		for i in ingredients:
			tasks.append(
				asyncio.create_task(
					player_demons_queries.set_demon_in_party(player_id, server_id, i.ing_id, set_in_party=False)
				)
			)

		# Set in party, update party stats and perform tasks.
		await asyncio.gather(
			player_demons_queries.set_demon_in_party(player_id, server_id, fused_demon.id, set_in_party=True),
			player_demons_queries.update_party(player_id, server_id, party_add=party_num_to_remove),
			*tasks,
		)

		# Add dupe level if already summoned.
		if is_summoned:
			dupe_message = None

			# Try applying dupe level.
			if fused_reg_status in {DemonRegistration.IN_PARTY, DemonRegistration.ON_LOAN, DemonRegistration.LEADER}:
				dupe_message = await encounter_utils.grant_dupe_reward(player_id, server_id, fused_demon)

			# Send dupe message if it exists.
			if dupe_message is not None:
				await MessageView.send(
					interaction.channel,
					FusionMsg.dupe_level_up(player_id, fused_demon, dupe_message),
					thumbnail=dd.profile_img,
					colour=dd.colour,
				)
				return
		# Add to compendium if not summoned.
		new_to_comp = await player_demons_queries.add_demon_to_compendium(
			player_id, server_id, fused_demon.id, fused_demon.rank
		)

		# Send final message.
		await MessageView.reply(
			interaction,
			FusionMsg.fusion_completed(fused_demon.race, fused_demon.name, new_to_comp=new_to_comp),
			thumbnail=dd.profile_img,
			colour=dd.colour,
		)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Fusion(bot))
