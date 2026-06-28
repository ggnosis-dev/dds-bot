import typing

import discord

from discord.ext import commands

import database_paths

from entities.command_data import SHOP_RAGS_COMMANDS, command_kwargs
from helpers import checks
from queries import item_queries
from shared_enums import Emotes

PAGE_SIZE = 5
SHOP_COLOUR = 0x1E452F


class RagsShop(commands.Cog):
	"""Cog for the Rags Shop where players can spend Rags to buy items."""

	def __init__(self, bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(SHOP_RAGS_COMMANDS, "rags"))
	async def rags_shop_command(self, ctx: commands.Context):
		"""Command to view the Rags Shop and trade gems for items."""
		view = RagsShopView(ctx.author.name)
		await ctx.send(view=view)


# TODO: Move this out of this file.
class RagsShopView(discord.ui.LayoutView):
	def __init__(self, user_name: str):
		super().__init__()
		self.user_name = user_name
		self.page = 1
		self.shop_items = database_paths.load_json(database_paths.ITEMS_JSON)
		self._build_shop_layout()

	class PageButton(discord.ui.Button):
		"""Custom button for navigating between pages of the compendium view."""

		def __init__(self, direction: str) -> None:
			if direction == "prev":
				super().__init__(label="<", style=discord.ButtonStyle.primary)
			elif direction == "next":
				super().__init__(label=">", style=discord.ButtonStyle.primary)
			else:
				raise ValueError("ERROR: Direction must be 'prev' or 'next'.")

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a page navigation button is clicked. Allows wrapping around the pages."""
			view = typing.cast(RagsShopView, self.view)

			if self.label == "<":
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == ">":
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			view.clear_items()
			view._build_shop_layout()
			await interaction.response.edit_message(view=view)

	def _build_shop_layout(self) -> None:
		"""Function to build Rag's Shop view layout."""
		ui = discord.ui
		container = ui.Container(accent_color=SHOP_COLOUR)
		page_entries = self._get_page_entries()
		page_nav = ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))

		container.add_item(ui.TextDisplay("### Rag's Shop"))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		for entry in page_entries:
			id, name, description, cost = entry
			gem_amounts = []

			for gem, amount in cost.items():
				gem_amounts.append(f"{gem.title()} x{amount}")

			button = discord.ui.Button(
				emoji=Emotes.ICON.value,
				style=discord.ButtonStyle.grey,
			)
			button.callback = self._purchase_callback(id)

			new_section = ui.Section(accessory=button)
			new_section.add_item(ui.TextDisplay(f"**{name}** - {', '.join(gem_amounts)}"))
			new_section.add_item(ui.TextDisplay(f"-# {description} "))

			container.add_item(new_section)

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f"-# Page {self.page} of {self.total_pages}"))
		container.add_item(page_nav)
		self.add_item(container)

	def _get_page_entries(self) -> list[dict]:
		page_list = []

		sorted_items = sorted(self.shop_items.items())

		for item_id, item_data in sorted_items:
			page_list.append((item_id, item_data["display_name"], item_data["description"], item_data["cost"]))

		self.total_pages = int(max(1, (len(page_list) + PAGE_SIZE - 1) / PAGE_SIZE))
		self.page = max(1, min(self.page, self.total_pages))

		start_index = (self.page - 1) * PAGE_SIZE
		end_index = start_index + PAGE_SIZE

		# Use delimiter to slice out entries.
		return page_list[start_index:end_index]

	def _purchase_callback(self, item_id: str):
		"""Callback for when an item purchase button is clicked."""

		async def callback(interaction: discord.Interaction) -> None:
			if item_id not in self.shop_items:
				raise RuntimeError(f"ERROR: Item with ID {item_id} not found in shop items.")

			item = self.shop_items[item_id]

			player = interaction.user
			server = typing.cast(discord.Guild, interaction.guild)

			check = item_queries.attempt_purchase_item(
				player_id=player.id, server_id=server.id, item_id=item_id, cost=item["cost"]
			)

			if not check:
				await interaction.response.send_message(
					f"You don't have enough gems to purchase a **{item['display_name']}**.", ephemeral=True
				)
				return

			await interaction.response.send_message(f"You have purchased a **{item['display_name']}**.", ephemeral=True)

		return callback


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(RagsShop(bot))
