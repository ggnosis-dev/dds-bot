from discord.ext import commands

from entities.command_data import SHOP_RAGS_COMMANDS, command_kwargs
from entities.item_data import ItemData
from helpers import checks
from queries import item_queries
from shared_enums import ShopColour
from views.shop_view import RagsShopView


class RagsShop(commands.Cog):
	"""Cog for the Rags Shop where players can spend Rags to buy items."""

	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(SHOP_RAGS_COMMANDS, "rags"))
	async def rags_shop_command(self, ctx: commands.Context):
		"""Command to view the Rags Shop and trade gems for items."""

		items = await item_queries.get_rags_item_list()
		view = RagsShopView(items, self._purchase_callback, ShopColour.RAGS.value)
		await ctx.send(view=view)

	# self.shop_items = database_paths.load_json(database_paths.ITEMS_JSON)
	async def _purchase_callback(self, interaction, item_data: ItemData) -> None:
		"""Callback for when an item purchase button is clicked."""

		player_id = interaction.user.id
		server_id = interaction.guild.id

		print(f"DEBUG: item_data: {item_data}")

		check = item_queries.attempt_purchase_item(
			player_id=player_id,
			server_id=server_id,
			item_id=item_data.item_id,
			cost=item_data.cost,
		)

		if not check:
			await interaction.response.send_message(
				f"You don't have enough gems to purchase a **{item_data.name}**.", ephemeral=True
			)
			return

		await interaction.response.send_message(f"You have purchased a **{item_data.name}**.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(RagsShop(bot))
