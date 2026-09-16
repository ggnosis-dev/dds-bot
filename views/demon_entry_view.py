import asyncio
import time

import discord

from entities.comp_data import DemonEntry, convert_row_to_demon_entry
from helpers.db import query_all
from shared_enums import Emotes, Unicode


class DemonEntryBrowser(discord.ui.LayoutView):
	"""Standard message wrapped in a embed like view."""

	def __init__(
		self,
		player_id: int,
		server_id: int,
		ordered_demon_ids: tuple[int],
		*,
		shown_demon_id: int | None = None,
	):
		super().__init__()
		self.player_id = player_id
		self.server_id = server_id
		self.ordered_dids = ordered_demon_ids
		self.shown_demon_id = shown_demon_id if shown_demon_id else ordered_demon_ids[0]
		self.data_cache: dict[int, DemonEntry] = {}

		self.total_pages = len(ordered_demon_ids)
		self.page = self._find_demon_index(self.shown_demon_id) + 1

	@classmethod
	async def send(
		cls,
		destination: discord.abc.Messageable,
		*args,
		shown_demon_id: int | None = None,
		**kwargs,
	) -> discord.Message:
		"""
		Send a message wrapped in an emebd type view.

		Args:
			destination: Where to send message to.
			*args: Required arguments (see init).
			**kwargs: Keyword/optional arguments (see init).
		"""
		try:
			view = cls(*args, shown_demon_id=shown_demon_id, **kwargs)
			await view.get_demon_entries(view.shown_demon_id)
			view._build_layout()
			return await destination.send(view=view)
		except Exception as e:
			raise (e)

	class PageButton(discord.ui.Button):
		"""Custom button for navigating between pages."""

		def __init__(self, direction: str) -> None:
			if direction == "prev":
				super().__init__(label="<", style=discord.ButtonStyle.primary)
			else:
				super().__init__(label=">", style=discord.ButtonStyle.primary)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a page navigation button is clicked. Allows wrapping around the pages."""

			view = self.view
			assert isinstance(view, DemonEntryBrowser), "Root view must use start() before followups can occur."

			if self.label == "<":
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == ">":
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			await asyncio.gather(
				view.refresh(),
				interaction.response.edit_message(view=view),
			)

	async def refresh(self) -> None:
		# Minus 1 as page is not index.
		await self.get_demon_entries(self.ordered_dids[self.page - 1])
		self.clear_items()
		self._build_layout()

	def _get_neighbouring_indexes(self, demon_id) -> tuple[int, int]:
		demon_index = self._find_demon_index(demon_id)
		list_length = len(self.ordered_dids)

		# Going below index 0 will wrap.
		prev_id = self.ordered_dids[demon_index - 1]

		# Going above the length will not, use modulo.
		next_id = self.ordered_dids[(demon_index + 1) % list_length]

		return prev_id, next_id

	def _find_demon_index(self, demon_id) -> int:
		# Get position of demon_id in the ordered list.
		for i, current_id in enumerate(self.ordered_dids):
			if current_id == demon_id:
				return i

		raise RuntimeError(f"demon_id {demon_id} not in ordered IDs")

	async def get_demon_entries(self, demon_id):
		# Assign demon_id to shown demon.
		self.shown_demon_id = demon_id

		prev_id, next_id = self._get_neighbouring_indexes(demon_id)

		# If prev, next or the current id is not in the cache already, append it to fetch.
		fetch_data = []
		for i in (prev_id, demon_id, next_id):
			if i not in self.data_cache:
				fetch_data.append(i)

		if fetch_data:
			rows = query_all(
				f"""
					SELECT
						v.*,
						pd.stored_rank,
						pd.dupes,
						pd.colour,
						pd.greeting,
						pd.date_met
					FROM demon_data_VIEW v
					JOIN player_demons pd
						ON pd.demon_id = v.id
						AND pd.player_id = ?
						AND pd.server_id = ?
					WHERE v.id IN ({",".join("?" * len(fetch_data))})
				""",
				(self.player_id, self.server_id, *fetch_data),
			)

			for r in rows:
				self.data_cache[r["id"]] = convert_row_to_demon_entry(r)

	def _build_layout(self) -> None:
		# Get the currently shown demon's data.
		shown_demon = self.data_cache[self.shown_demon_id]
		design_data = shown_demon.design_data
		date_met = time.strftime("%d-%b-%Y", time.gmtime(shown_demon.date_met))

		# Add a space in the hints for proper spacing with bullets.
		stored_rank_hint = f" (**{shown_demon.stored_rank}**)" if shown_demon.stored_rank != shown_demon.initial_rank else ""
		dupe_level_hint = (
			f" Level: **{shown_demon.dupes}** {Emotes.GEM.value}{Unicode.BULLET.value}" if shown_demon.dupes > 0 else ""
		)

		ui = discord.ui
		container = ui.Container(accent_color=design_data.colour)

		# Thumbnail section.
		section = ui.Section(accessory=ui.Thumbnail(media=design_data.profile_img))
		section.add_item(
			ui.TextDisplay(
				f"{Emotes.BLANK.value}"
				f"\n### `> {shown_demon.race} {shown_demon.name}`"
				f"\n-# Rank: **{shown_demon.initial_rank}**{stored_rank_hint} {Unicode.BULLET.value}"
				f"{dupe_level_hint}"
				f" Recruited: **{date_met}**"
			)
		)
		container.add_item(section)

		# Infobox portion.
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(
			ui.TextDisplay(
				f"\n-# - Tone: {shown_demon.tone_name.title()}"
				f"\n-# - Gems: {' & '.join(shown_demon.gems).title()}"
				f"\n-# - Origin: {shown_demon.origin or 'N/A.'}"
				# f"\n-# - Time Period: {'19th Century'}"
			)
		)

		# Description portion.
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f"{shown_demon.desc or 'No Description Available.'}"))

		# Add image.
		container.add_item(
			discord.ui.MediaGallery(
				discord.MediaGalleryItem(
					design_data.encounter_img,
					description=shown_demon.name,
				),
			)
		)

		container = self._build_footer(container)

		self.add_item(container)

	def _build_footer(self, container: discord.ui.Container) -> discord.ui.Container:
		"""Footer shows number of pages and given there's more than one page, will create page navigation."""
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(discord.ui.TextDisplay(f"-# Entry {self.page} of {self.total_pages}"))

		if self.total_pages != 1:
			page_nav = discord.ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))
			container.add_item(page_nav)

		return container
