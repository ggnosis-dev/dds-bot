import asyncio

from abc import abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any, Generic

import discord

from entities.fusion_data import SpecialFusionShopData
from entities.item_data import ShopItemData, ShopItemGroup
from entities.view_data import SHOP_PAGE_SIZE
from helpers.messages import ShopMsgs
from shared_enums import Banners, EmbedColours, Emotes
from views.common_view import BaseLayoutView, EntryT, ResponseView

# Generic type.
type PurchaseCallback[EntryT] = Callable[[discord.Interaction, EntryT, int], Coroutine[Any, Any, None]]


class BaseShopView(BaseLayoutView, Generic[EntryT], discord.ui.LayoutView):
	def __init__(
		self,
		player_id: int,
		entries: list[EntryT],
		on_purchase: PurchaseCallback[EntryT],
		*,
		page: int,
		colour: int,
	) -> None:
		super().__init__(entries, page=page, page_size=SHOP_PAGE_SIZE, colour=colour)

		self.player_id = player_id
		self.items = entries
		self.on_purchase = on_purchase
		self.show_info = False

		self.refresh()

	@classmethod
	async def send(
		cls,
		destination: discord.abc.Messageable,
		player_id: int,
		entries: list[EntryT],
		on_purchase: PurchaseCallback[EntryT],
		page: int = 1,
		colour: int = EmbedColours.DEFAULT.value,
	) -> discord.Message:
		view = cls(player_id, entries, on_purchase, page=page, colour=colour)
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
			await self.on_purchase(interaction, item, self.player_id)

		return callback


class RagsShopView(BaseShopView[ShopItemData | ShopItemGroup]):
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

	def _get_title_desc(self, entry: ShopItemData | ShopItemGroup) -> tuple[str, ...]:
		item_options = entry.options if isinstance(entry, ShopItemGroup) else [entry]

		# title = ShopMsgs.build_item_title(entry.name, entry.cost)
		title = ShopMsgs.build_item_title(entry.name)
		# desc = ShopMsgs.build_item_desc(entry.description)
		desc = ShopMsgs.build_item_cost(item_options)
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


# class RagsShopModal(discord.ui.Modal):
# 	def __init__(
# 		self,
# 		entries: list[ShopItemData],
# 		title: str,
# 		*,
# 		timeout: int = 180,
# 		ephemeral_response: bool = True,
# 	):
# 		super().__init__(title=title, timeout=timeout)

# 		self.entries = sorted(entries, key=lambda i: i.item_id)
# 		self.ephemeral_response = ephemeral_response
# 		self._build_modal()

# 	async def on_submit(self, interaction: discord.Interaction):
# 		await interaction.response.send_message(f"Test {self.option.label}", ephemeral=self.ephemeral_response)

# 	def _build_modal(self):
# 		# TODO: Build an image with Emotes here.
# 		self.add_item(
# 			discord.ui.TextDisplay(
# 				content=f"{Emotes.GEM.value}{Emotes.GEM.value}{Emotes.GEM.value} How many would you like?"
# 			)
# 		)

# 		if len(self.entries) > 1:
# 			options = [
# 				discord.SelectOption(label=i.name, description=i.description, value=str(i.item_id)) for i in self.entries
# 			]
# 			select = discord.ui.Select(options=options)
# 			self.add_item(discord.ui.Label(text="Select The Item", component=select))

# 		option = discord.ui.TextInput(
# 			style=discord.TextStyle.short,
# 			default="1",
# 			required=True,
# 			max_length=2,
# 		)
# 		self.add_item(discord.ui.Label(text="Quantity", component=option))
# 		self.add_item(discord.ui.TextDisplay(content="-# That'll cost you ."))

# 		self.option = option


class RagsBuyView(ResponseView):
	def __init__(self, entries: list[ShopItemData], exclusive_to: int):
		super().__init__(exclusive_to=exclusive_to, timeout=180.0)
		self.entries = entries
		self.item = entries[0]
		self.qty = 1

		# These ui items will get updated.
		self.cost_text = discord.ui.TextDisplay(content=self._cost())

		self.select = None
		if len(entries) > 1:
			self.select = discord.ui.Select(
				options=[
					discord.SelectOption(
						label=i.name,
						description=i.description,
						value=str(i.item_id),
					)
					for i in entries
				],
			)
			self.select.callback = self.on_select

		self.minus_btn = discord.ui.Button(label="-")
		self.minus_btn.callback = self.on_minus
		self.plus_btn = discord.ui.Button(label="+")
		self.plus_btn.callback = self.on_plus
		self.buy_btn = discord.ui.Button(label="Trade", style=discord.ButtonStyle.success)
		self.buy_btn.callback = self.on_buy

		self._build_layout()

	def _build_layout(self) -> None:
		# Changes to specific UI elements.
		self.cost_text.content = self._cost()
		self.minus_btn.style = discord.ButtonStyle.primary if self.qty > 1 else discord.ButtonStyle.secondary
		self.plus_btn.style = discord.ButtonStyle.primary if self.qty < 99 else discord.ButtonStyle.secondary

		container = discord.ui.Container(accent_color=EmbedColours.RAGS.value)
		container.add_item(self.cost_text)

		if self.select is not None:
			container.add_item(discord.ui.ActionRow(self.select))

		container.add_item(discord.ui.ActionRow(self.minus_btn, self.plus_btn, self.buy_btn))

		if self.timed_out:
			container.add_item(discord.ui.TextDisplay("-# Timed Out"))

		self.add_item(container)

	def _cost(self) -> str:
		item_costs: list = self.item.cost

		gems_required_parts = []
		for i in item_costs:
			gems_required_parts.append(f"{i.amount * self.qty} {i.name}")

		cost = " + ".join(gems_required_parts)
		return f"{self.qty}x **{self.item.name}** will cost you...\n-# {cost}"

	async def on_select(self, interaction: discord.Interaction):
		assert self.select, "Can't reach here with a None select."

		selected_id = int(self.select.values[0])
		for e in self.entries:
			if e.item_id == selected_id:
				self.item = e
				break
		await self.refresh(interaction)

	async def on_plus(self, interaction):
		self.qty = min(self.qty + 1, 99)
		await self.refresh(interaction)

	async def on_minus(self, interaction):
		self.qty = max(self.qty - 1, 1)
		await self.refresh(interaction)

	async def on_buy(self, interaction):
		self.on_finish()
		await interaction.response.edit_message(view=self)

	async def refresh(self, interaction: discord.Interaction) -> None:
		self.clear_items()
		self._build_layout()
		await interaction.response.edit_message(view=self)
