import asyncio

import discord

from entities.demon_data import DemonData, convert_row_to_demon_data
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
		shown_demon_id: int,
	):
		super().__init__()
		self.player_id = player_id
		self.server_id = server_id
		self.ordered_dids = ordered_demon_ids
		self.shown_demon_id = shown_demon_id
		self.data_cache: dict[int, DemonData] = {}

	@classmethod
	async def send(
		cls,
		destination: discord.abc.Messageable,
		*args,
		shown_demon_id: int,
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
			await view.get_demon_entries(shown_demon_id)
			view._build_layout()
			return await destination.send(view=view)
		except Exception as e:
			raise (e)

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
						pd.dupes,
						pd.colour,
						pd.greeting
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
				self.data_cache[r["id"]] = convert_row_to_demon_data(r)
				print(self.data_cache)

	def _build_layout(self) -> None:
		# Get the currently shown demon's data.
		shown_demon = self.data_cache[self.shown_demon_id]
		design_data = shown_demon.design_data

		ui = discord.ui
		container = ui.Container(accent_color=design_data.colour)

		# Thumbnail section.
		section = ui.Section(accessory=ui.Thumbnail(media=design_data.profile_img))
		section.add_item(
			ui.TextDisplay(
				f"{Emotes.BLANK.value}"
				f"\n### {shown_demon.race} {shown_demon.name}"
				f"\n-# Rank: **{shown_demon.rank}** (**{32}**) {Unicode.BULLET.value}"
				f" Level: **{shown_demon.dupes}** {Emotes.GEM.value} {Unicode.BULLET.value}"
				f" Recruited: **10/10/2025**"
			)
		)
		container.add_item(section)

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		container.add_item(
			ui.TextDisplay(
				f"\n-# - Tone: {shown_demon.tone_type.name.title()}"
				f"\n-# - Gems: {' & '.join(shown_demon.gems).title()}"
				f"\n-# - Origin: {'Dictionnaire Infernal'}"
				f"\n-# - Time Period: {'19th Century'}"
			)
		)

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		container.add_item(
			ui.TextDisplay(
				"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed ligula ante, dapibus ac pretium eget, dictum sed eros. Vestibulum semper ut nibh quis tincidunt. Curabitur iaculis dui felis, maximus mollis nisi porttitor quis. Ut bibendum velit eros, in tincidunt felis imperdiet et. Aliquam erat volutpat. Curabitur eget pulvinar orci. In hac habitasse platea dictumst. Sed ac lacus sit amet nisi malesuada vulputate. Nam blandit non felis vitae egestas. Integer viverra condimentum enim, eu dignissim nisi gravida eget. Cras ultricies interdum magna, eget viverra mauris lobortis in. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Nulla porttitor egestas ornare. Donec orci mauris, pharetra eget porttitor nec, malesuada eu turpis. "
			)
		)

		# Add image.
		container.add_item(
			discord.ui.MediaGallery(
				discord.MediaGalleryItem(
					design_data.encounter_img,
					description=shown_demon.name,
				),
			)
		)

		self.add_item(container)
