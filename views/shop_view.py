from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any, Generic, TypeVar, cast

import discord

from entities.item_data import ItemData
from shared_enums import Emotes

T = TypeVar("T")
type PurchaseCallback[T] = Callable[[discord.Interaction, str, T], Coroutine[Any, Any, None]]

PAGE_SIZE = 5
SHOP_COLOUR = 0x1E452F


class BaseShopView(ABC, Generic[T], discord.ui.LayoutView):
	def __init__(
		self,
		items: list[T],
		on_purchase: PurchaseCallback[T],
		colour: int = SHOP_COLOUR,
	) -> None:
		super().__init__()

		self.items = items
		self.on_purchase = on_purchase
		self.colour = colour
		self.page = 1

		self._build_shop_layout()

	class PageButton(discord.ui.Button):
		"""Custom button for navigating between pages of the shop view."""

		def __init__(self, direction: str) -> None:
			if direction == "prev":
				super().__init__(label="<", style=discord.ButtonStyle.primary)
			else:
				super().__init__(label=">", style=discord.ButtonStyle.primary)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a page navigation button is clicked. Allows wrapping around the pages."""

			view = cast(BaseShopView, self.view)

			if self.label == "<":
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == ">":
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			view.clear_items()
			view._build_shop_layout()
			await interaction.response.edit_message(view=view)

	@abstractmethod
	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		pass

	@abstractmethod
	def _build_shop_layout(self) -> None:
		pass

	def _get_page_entries(self) -> list[T]:
		self.total_pages = int(max(1, (len(self.items) + PAGE_SIZE - 1) / PAGE_SIZE))
		self.page = max(1, min(self.page, self.total_pages))

		start_index = (self.page - 1) * PAGE_SIZE
		end_index = start_index + PAGE_SIZE

		# Use delimiter to slice out entries.
		return self.items[start_index:end_index]

	def _build_footer(self, container: discord.ui.Container) -> discord.ui.Container:
		"""Footer shows number of pages and given there's more than one page, will create page navigation."""
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(discord.ui.TextDisplay(f"-# Page {self.page} of {self.total_pages}"))

		if self.total_pages != 1:
			page_nav = discord.ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))
			container.add_item(page_nav)

		return container

	def _make_purchase_callback(self, item_id: str, item: T):
		async def callback(interaction: discord.Interaction) -> None:
			await self.on_purchase(interaction, item_id, item)

		return callback


class RagsShopView(BaseShopView[ItemData]):
	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(discord.ui.TextDisplay("### Rag's Shop"))
		container.add_item(
			discord.ui.TextDisplay(
				"-# **RAG:**\n-# Mmmm... You smell strongly of gems. Welcome. I'll trade anything with you."
			)
		)
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		container.add_item(
			discord.ui.TextDisplay(
				"-# - Trade gemstones for incense that can be used to increase the rank of one of your demons."
				"\n-# - Each demon requires an incense of their respective race."
				"\n-# - As the demon grows in strength, larger incense will be required."
			)
		)
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		return container

	def _build_shop_layout(self) -> None:
		"""Function to build Rag's Shop view layout."""

		container = discord.ui.Container(accent_color=SHOP_COLOUR)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		for item in page_entries:
			container = self._build_page_entry(container, item)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_page_entry(
		self,
		container: discord.ui.Container,
		item: ItemData,
	) -> discord.ui.Container:
		cost = item.cost
		gem_amounts = []

		for gem, amount in cost.items():
			gem_amounts.append(f"{gem.title()} x{amount}")

		# Set up buttons.
		button = discord.ui.Button(
			emoji=Emotes[item.emote].value,
			style=discord.ButtonStyle.grey,
		)
		button.callback = self._make_purchase_callback(item.item_id, item)

		new_section = discord.ui.Section(accessory=button)
		new_section.add_item(discord.ui.TextDisplay(f"**{item.name}** - {', '.join(gem_amounts)}"))
		new_section.add_item(discord.ui.TextDisplay(f"-# {item.description} "))

		container.add_item(new_section)
		return container
