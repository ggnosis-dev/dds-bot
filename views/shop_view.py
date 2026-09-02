from abc import abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any, Generic

import discord

from entities.fusion_data import SpecialFusionShopData
from entities.item_data import ShopItemData
from entities.view_data import SHOP_PAGE_SIZE
from helpers.messages import ShopMsgs
from shared_enums import Banners, EmbedColours, Emotes
from views.common_view import BaseLayoutView, EntryT

# Generic type.
type PurchaseCallback[EntryT] = Callable[[discord.Interaction, EntryT], Coroutine[Any, Any, None]]


class BaseShopView(BaseLayoutView, Generic[EntryT], discord.ui.LayoutView):
	def __init__(
		self,
		entries: list[EntryT],
		on_purchase: PurchaseCallback[EntryT],
		*,
		page: int,
		colour: int,
	) -> None:
		super().__init__(entries, page=page, page_size=SHOP_PAGE_SIZE, colour=colour)

		self.items = entries
		self.on_purchase = on_purchase
		self.show_info = False

		self.refresh()

	@classmethod
	async def send(
		cls,
		destination: discord.abc.Messageable,
		entries: list[EntryT],
		on_purchase: PurchaseCallback[EntryT],
		page: int = 1,
		colour: int = EmbedColours.DEFAULT.value,
	) -> discord.Message:
		view = cls(entries, on_purchase, page=page, colour=colour)
		return await destination.send(view=view)

	@abstractmethod
	def _get_title_desc(self, entry: EntryT) -> tuple[str, ...]:
		pass

	def _build_page_entry(
		self, container: discord.ui.Container, entry: EntryT, title: str, desc: str, emote: str
	) -> discord.ui.Container:
		# Set up buttons.
		button = discord.ui.Button(
			emoji=emote,
			style=discord.ButtonStyle.grey,
		)
		button.callback = self._make_purchase_callback(entry)

		# Set up new item section.
		new_section = discord.ui.Section(accessory=button)
		new_section.add_item(discord.ui.TextDisplay(title))
		new_section.add_item(discord.ui.TextDisplay(desc))
		container.add_item(new_section)

		return container

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
			title, desc, emote = self._get_title_desc(item)
			container = self._build_page_entry(container, item, title, desc, emote)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		# Build banner at top of view.
		container.add_item(
			discord.ui.MediaGallery(
				discord.MediaGalleryItem(
					Banners.RAGS.value,
					description="Rag's Jewelry",
				),
			)
		)

		# Build information button with section.
		info_button = self.InfoButton(self.show_info)
		section = discord.ui.Section(accessory=info_button)
		section.add_item(discord.ui.TextDisplay(ShopMsgs.rags_dialogue()))
		container.add_item(section)

		# Show information if needed.
		if self.show_info:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
			container.add_item(discord.ui.TextDisplay(ShopMsgs.rags_info()))
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		else:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _get_title_desc(self, entry: ShopItemData) -> tuple[str, ...]:
		title = ShopMsgs.build_item_title(entry.name, entry.cost)
		desc = ShopMsgs.build_item_desc(entry.description)
		emote = entry.emote.value or Emotes.GEM.value
		return title, desc, emote


class SpecialFusionView(BaseShopView[SpecialFusionShopData]):
	def _build_layout(self) -> None:
		"""Function to build Special Fusion's Shop view layout."""

		container = discord.ui.Container(accent_color=self.colour)
		page_entries = self._get_page_entries()

		container = self._build_header(container)
		for entry in page_entries:
			title, desc, emote = self._get_title_desc(entry)
			container = self._build_page_entry(container, entry, title, desc, emote)
		container = self._build_footer(container)

		self.add_item(container)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		# Build banner at top of view.
		container.add_item(
			discord.ui.MediaGallery(
				discord.MediaGalleryItem(
					Banners.SP_FUSION.value,
					description="Special Fusion",
				),
			)
		)

		# Build information button with section.
		info_button = self.InfoButton(self.show_info)
		section = discord.ui.Section(accessory=info_button)
		section.add_item(discord.ui.TextDisplay(ShopMsgs.mido_dialogue()))
		container.add_item(section)

		# Show information if needed.
		if self.show_info:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
			container.add_item(discord.ui.TextDisplay(ShopMsgs.special_fusion_info()))
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		else:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		return container

	def _get_title_desc(self, entry: SpecialFusionShopData) -> tuple[str, ...]:
		title = ShopMsgs.build_sp_fusion_title(entry.race, entry.name, entry.rank)
		required = ShopMsgs.build_sp_fusion_required(entry.ingredients)
		emote = Emotes.ICON.value
		return title, required, emote
