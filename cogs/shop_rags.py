from discord.ext import commands

from entities.command_data import SHOP_RAGS_COMMANDS, command_kwargs
from entities.item_data import ShopItemData
from helpers import checks
from helpers.messages import ShopMsgs as Messages
from queries import item_queries
from shared_enums import EmbedColours
from views.common_view import MessageView
from views.shop_view import RagsShopView


class Shop(commands.Cog):
	"""Cog for the Rags Shop where players can spend Rags to buy items."""

	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(SHOP_RAGS_COMMANDS, "rags"))
	async def rags_shop_command(self, ctx: commands.Context):
		"""Command to view the Rags Shop and trade gems for items."""

		items = await item_queries.get_rags_item_list()
		await RagsShopView.send(ctx.channel, items, self._purchase_callback, colour=EmbedColours.RAGS.value)

	async def _purchase_callback(self, interaction, item_data: ShopItemData) -> None:
		"""Callback for when an item purchase button is clicked."""

		player_id = interaction.user.id
		server_id = interaction.guild.id
		check = await item_queries.attempt_purchase_item(player_id, server_id, item_data.item_id, item_data.cost)

		if not check:
			await MessageView.reply(interaction, Messages.not_enough_gems(item_data.name), ephemeral=True)
			return
		await MessageView.reply(interaction, Messages.purchase_success(item_data.name), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Shop(bot))
