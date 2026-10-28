from discord.ext import commands

from entities.command_data import SHOP_RAGS_COMMANDS, command_kwargs
from entities.item_data import ShopItemData, ShopItemGroup
from helpers import checks, gets
from helpers.messages import ShopMsgs as Messages
from queries import item_queries
from shared_enums import EmbedColours
from views.common_view import MessageView
from views.shop_view import RagsBuyView, RagsShopView


class Shop(commands.Cog):
	"""Cog for the Rags Shop where players can spend Rags to buy items."""

	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(SHOP_RAGS_COMMANDS, "rags"))
	async def rags_shop_command(self, ctx: commands.Context):
		"""Command to view the Rags Shop and trade gems for items."""

		player_id = gets.get_player_id(ctx)
		items = await item_queries.get_rags_item_list()
		await RagsShopView.send(ctx.channel, player_id, items, self._purchase_callback, colour=EmbedColours.RAGS.value)

	async def _purchase_callback(self, interaction, item_data: ShopItemData | ShopItemGroup, player_id: int) -> None:
		"""Callback for when an item purchase button is clicked."""

		item_options = item_data.options if isinstance(item_data, ShopItemGroup) else [item_data]

		# Open the modal.
		user_id = gets.get_user_id(interaction)
		view = RagsBuyView(item_options, user_id)
		await interaction.response.send_message(view=view)

		if await view.wait_for_response():
			print("PASSED")
			# TODO: Update this for Groups.
			check = await item_queries.attempt_purchase_item(player_id, item_data.item_id, item_data.cost)

			if not check:
				await MessageView.reply(interaction, Messages.not_enough_gems(item_data.name), ephemeral=True)
				return
			await MessageView.reply(interaction, Messages.purchase_success(item_data.name), ephemeral=True)

			if item_data.name.lower() == "fairy incense":
				interaction.client.dispatch("tutorial_trigger", interaction, "rags_fairy")


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Shop(bot))
