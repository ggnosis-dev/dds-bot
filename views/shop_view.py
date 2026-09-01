from collections.abc import Callable, Coroutine
from typing import Any, Generic

import discord

from entities.fusion_data import SpecialFusionShopData
from entities.item_data import ShopItemData
from entities.view_data import SHOP_PAGE_SIZE
from shared_enums import Banners, EmbedColours, Emotes
from views.common_view import BaseLayoutView, EntryT

# Generic type.
type PurchaseCallback[EntryT] = Callable[[discord.Interaction, EntryT], Coroutine[Any, Any, None]]


class BaseShopView(BaseLayoutView, Generic[EntryT], discord.ui.LayoutView):
	def __init__(
		self,
		entries: list[EntryT],
		on_purchase: PurchaseCallback[EntryT],
		page: int = 1,
		colour: int = EmbedColours.DEFAULT.value,
	) -> None:
		super().__init__(entries, page=page, page_size=SHOP_PAGE_SIZE, colour=colour)

		self.items = entries
		self.on_purchase = on_purchase
		self.show_info = False

		self.refresh()

	def _make_purchase_callback(self, item: EntryT):
		async def callback(interaction: discord.Interaction) -> None:
			await self.on_purchase(interaction, item)

		return callback


class RagsShopView(BaseShopView[ShopItemData]):
	def _build_layout(self) -> None:
		"""Function to build Rag's Shop view layout."""

		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		for item in page_entries:
			container = self._build_page_entry(container, item)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(
			discord.ui.MediaGallery(
				discord.MediaGalleryItem(
					Banners.RAGS.value,
					description="Rag's Jewelry",
				),
			)
		)

		info_button = self.InfoButton(self.show_info)
		section = discord.ui.Section(accessory=info_button)
		section.add_item(
			discord.ui.TextDisplay(
				"-# **RAG:**\n-# Mmmm... You smell strongly of gems. Welcome. I'll trade anything with you."
			)
		)
		container.add_item(section)

		if self.show_info:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

			container.add_item(
				discord.ui.TextDisplay(
					"-# - Trade gemstones for incense that can be used to increase the rank of one of your demons."
					"\n-# - Each demon requires an incense for their respective race."
					"\n-# - As the demon grows in strength, larger incense will be required. (NOT YET IMPLEMENTED)"
				),
			)

			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		else:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _build_page_entry(
		self,
		container: discord.ui.Container,
		item: ShopItemData,
	) -> discord.ui.Container:
		cost = item.cost
		gem_amounts = []

		for gem, amount in cost.items():
			gem_amounts.append(f"{gem.title()} x{amount}")

		# Set up buttons.
		button = discord.ui.Button(
			emoji=item.emote.value,
			style=discord.ButtonStyle.grey,
		)
		button.callback = self._make_purchase_callback(item)

		new_section = discord.ui.Section(accessory=button)
		new_section.add_item(discord.ui.TextDisplay(f"**{item.name}** - {', '.join(gem_amounts)}"))
		new_section.add_item(discord.ui.TextDisplay(f"-# {item.description} "))

		container.add_item(new_section)
		return container


class SpecialFusionView(BaseShopView[SpecialFusionShopData]):
	def _build_layout(self) -> None:
		"""Function to build Rag's Shop view layout."""

		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		for entry in page_entries:
			container = self._build_page_entry(container, entry)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		container.add_item(
			discord.ui.MediaGallery(
				discord.MediaGalleryItem(
					Banners.SP_FUSION.value,
					description="Special Fusion",
				),
			)
		)

		info_button = self.InfoButton(self.show_info)
		section = discord.ui.Section(accessory=info_button)
		section.add_item(
			discord.ui.TextDisplay("-# **MIDO:**\n-# Welcome to the Cathedral of Shadows, where demons gather...")
		)
		container.add_item(section)

		if self.show_info:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

			container.add_item(
				discord.ui.TextDisplay(
					"-# - Perform a Special Fusion by sacrificing the necessary demons from your party."
					"\n-# - Special Fusion Keys can be found by leveling up the server and through events."
				),
			)

			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		else:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _build_page_entry(
		self,
		container: discord.ui.Container,
		entry: SpecialFusionShopData,
	) -> discord.ui.Container:
		ing = entry.ingredients
		ingredient_list = []

		for i in ing:
			ingredient_list.append(f"{i.race} {i.name}")

		# Set up buttons.
		button = discord.ui.Button(
			emoji=Emotes.ICON.value,
			style=discord.ButtonStyle.grey,
		)
		button.callback = self._make_purchase_callback(entry)

		new_section = discord.ui.Section(accessory=button)
		new_section.add_item(discord.ui.TextDisplay(f"**{entry.race} {entry.name}** (Rank {entry.rank})"))
		new_section.add_item(discord.ui.TextDisplay(f"-# **Required:** {' + '.join(ingredient_list)}"))

		container.add_item(new_section)
		return container
