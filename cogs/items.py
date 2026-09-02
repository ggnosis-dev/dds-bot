import asyncio

from typing import cast

import discord

from discord.ext import commands

from entities.command_data import GEMS_COMMANDS, ITEMS_COMMANDS, command_kwargs
from entities.demon_data import DemonData
from entities.item_data import INCENSE_RANK_INCREASE
from entities.view_data import Columns
from helpers import checks, gets, utils
from helpers.messages import ItemMsg
from queries import demon_queries, gem_queries, item_queries, player_demons_queries, server_queries
from shared_enums import DemonRegistration
from views.common_view import ConfirmationView, MessageView
from views.table_view import GemCollectionView, InventoryView


class InventoryCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(ITEMS_COMMANDS, "use"))
	async def use_command(self, ctx: commands.Context, *, input_str: str | None) -> None:
		"""Use an item on a demon. "item_name; demon_name; opt: amount_to_use"."""

		# Get and validate player input.
		parts = utils.split_input_str(input_str, maximum=3)
		if len(parts) < 2:
			await MessageView.send(ctx.channel, ItemMsg.no_input_given(ITEMS_COMMANDS["use"]))
			return

		item_name = parts[0]
		demon_name = parts[1]
		number_to_use = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
		if number_to_use <= 0:
			number_to_use = 1
		player_id, server_id = gets.get_player_server_ids(ctx)
		item_id = await item_queries.get_item_id_by_name(item_name)

		# Check if item is valid.
		if item_id is None:
			await MessageView.send(ctx.channel, ItemMsg.item_doesnt_exist(item_name))
			return

		# UX check for impossible action if player does not have enough of the item.
		quantity = await item_queries.get_player_has_item(player_id, server_id, item_id)
		if quantity < number_to_use:
			await MessageView.send(ctx.channel, ItemMsg.not_in_inventory(item_name))
			return

		# Get target demon ID.
		demon_id = await demon_queries.get_demon_id_by_name(demon_name)
		if demon_id is None:
			await MessageView.send(ctx.channel, ItemMsg.not_in_party(demon_name))
			return

		# Demon is not a part of the race that can use the item.
		can_use = await item_queries.can_demon_use_item(demon_id, item_id)
		if not can_use:
			await MessageView.send(ctx.channel, ItemMsg.exclusive_to_fail(demon_name, item_name))
			return

		# Check registration status. If ON LOAN, do not rank up.
		reg_status = await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
		if reg_status == DemonRegistration.ON_LOAN:
			await MessageView.send(ctx.channel, ItemMsg.currently_on_loan(demon_name))
			return

		if reg_status not in {DemonRegistration.IN_PARTY, DemonRegistration.LEADER}:
			await MessageView.send(ctx.channel, ItemMsg.not_in_party(demon_name))
			return

		# Get confirmation to use item.
		confirmed = await ConfirmationView.send(
			ctx.channel, ItemMsg.confirm_use_item(quantity, item_name, number_to_use, demon_name), player_id
		)
		if not confirmed:
			return

		# Use the incense item and apply its effect.
		used_item = await item_queries.use_incense(player_id, server_id, demon_id, item_id, number_to_use)
		if used_item:
			dd = await demon_queries.get_design_data(demon_id)
			message = ItemMsg.use_item_completed(player_id, item_name, demon_name, number_to_use * INCENSE_RANK_INCREASE)
			await MessageView.send(ctx.channel, message, thumbnail=dd.profile_img, colour=dd.colour)
			return

		# Second, non-UX check of not in inventory message if used_item fails (usually from double command running).
		await MessageView.send(ctx.channel, ItemMsg.not_in_inventory(item_name))

	@checks.has_profile()
	@commands.command(**command_kwargs(ITEMS_COMMANDS, "inventory"))
	async def item_inventory_command(self, ctx: commands.Context) -> None:
		"""View player's item inventory."""

		player, server = gets.get_player_server(ctx)
		items = await item_queries.get_player_inventory(player.id, server.id)
		columns = list(Columns.ITEM_DEFAULT)
		columns.append(Columns.DESC)

		if not items:
			await MessageView.send(ctx.channel, ItemMsg.empty_inventory())
			return

		await InventoryView.send(ctx.channel, items, columns, player.name)


class GemCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(GEMS_COMMANDS, "gems"))
	async def gems_command(self, ctx: commands.Context) -> None:
		"""View player's current gems collection."""
		player, server = gets.get_player_server(ctx)
		collected_gems = await gem_queries.get_player_gems(player.id, server.id)
		columns = list(Columns.ITEM_DEFAULT)

		await GemCollectionView.send(ctx.channel, collected_gems, columns, player.name)

	@checks.has_profile()
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message) -> None:
		"""
		Listener for player messages to track progress towards finding a gem.
		Only triggers if player has a profile.
		"""
		try:
			# Exit early if message is from bot or not in a server.
			if message.author.bot or message.guild is None:
				return

			ctx = await self.bot.get_context(message)

			# This check will exit if the player uses a proper command.
			if ctx.valid:
				return

			player_id, server_id = gets.get_player_server_ids(ctx)
			selected_demon_id = await player_demons_queries.get_selected_demon_id(player_id, server_id)

			if selected_demon_id is None:
				return

			# Increase exp towards finding a gem.
			gem_found = await gem_queries.increase_gem_meter(player_id, server_id, selected_demon_id)

			if gem_found:
				d = cast(DemonData, demon_queries.get_demon_by_id(player_id, server_id, selected_demon_id))

				new_gem, set_channel = await asyncio.gather(
					gem_queries.add_gem(player_id, server_id, d.gems),
					server_queries.get_dedicated_channel(server_id),
				)

				send_to_channel = self.bot.get_channel(set_channel) if set_channel else ctx.channel

				await MessageView.send(
					send_to_channel,
					ItemMsg.found_gem(player_id, d.name, new_gem),
					d.design_data.profile_img,
					d.design_data.colour,
				)
		except Exception as e:
			raise RuntimeError(f"GemCommands | on_message | {e}")


class Items(InventoryCommands, GemCommands):
	def __init__(self, bot):
		self.bot = bot


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Items(bot))
