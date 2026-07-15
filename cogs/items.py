from discord.ext import commands

from entities.command_data import ITEMS_COMMANDS, command_kwargs
from entities.view_data import Columns
from helpers import checks, gets
from queries import demon_queries, item_queries, player_demons_queries
from shared_enums import DemonRegistration
from views.table_view import InventoryView


class Items(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(ITEMS_COMMANDS, "use"))
	async def use_item_command(self, ctx: commands.Context, *, input_str: str) -> None:
		"""
		Use an item on a demon.

		Args:
			input_str (str): String containing item name and optional demon name, separated by a semicolon delimiter.
				"item_name; demon_name" or just "item_name" to use on selected demon.
		"""

		parts = input_str.split(";")
		item_name = parts[0].strip().title()
		demon_name = parts[1].strip().title() if len(parts) > 1 else None
		player_id, server_id = gets.get_player_server_ids(ctx)
		item_id = item_queries.get_item_id_by_name(item_name)
		demon_id = None

		# Check if item is valid.
		if item_id is None:
			await ctx.send(f"The item **{item_name}** does not exist in your inventory.")
			return

		# Check if player has the item.
		if not item_queries.get_player_has_item(player_id, server_id, item_id):
			await ctx.send(f"You don't have any **{item_name}** in your inventory.")
			return

		# Get target demon ID.
		if demon_name:
			demon_id = demon_queries.get_demon_id_by_name(demon_name)

			if demon_id is None:
				await ctx.send(f"A **{demon_name}** was not found in your party...")
				return
		else:
			demon_id = await player_demons_queries.get_selected_demon_id(player_id, server_id)

			# No demon was specified in command, and player doesn't have a demon selected.
			if demon_id is None:
				await ctx.send("You don't have a demon selected. Use `>select` to choose a demon first.")
				return

		# Check if in player's party.
		if (
			await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
			!= DemonRegistration.IN_PARTY
		):
			await ctx.send(f"A **{demon_name}** was not found in your party...")
			return

		# Use the incense item and apply its effect.
		if item_queries.use_incense(player_id, server_id, demon_id, item_id):
			demon_name = demon_queries.get_demon_name_by_id(demon_id)
			await ctx.send(
				(f"<@{player_id}> used **{item_name}** on **{demon_name}**! Their rank has **increased** by **3**."),
			)

	@checks.has_profile()
	@commands.command(**command_kwargs(ITEMS_COMMANDS, "inventory"))
	async def item_inventory_command(self, ctx: commands.Context) -> None:
		"""View player's item inventory."""

		player, server = gets.get_player_server(ctx)
		items = await item_queries.get_player_inventory(player.id, server.id)
		columns = list(Columns.ITEM_DEFAULT)

		if not items:
			await ctx.send("Your inventory is empty.")
			return

		view = InventoryView(player.name, items, columns)
		await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Items(bot))
