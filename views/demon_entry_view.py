import asyncio

import discord

from entities.demon_data import convert_row_to_demon_data
from helpers.db import query_all
from shared_enums import EmbedColours


class DemonEntryBrowser(discord.ui.LayoutView):
	"""Standard message wrapped in a embed like view."""

	def __init__(
		self,
		player_id: int,
		server_id: int,
		ordered_demon_ids: tuple[int],
	):
		super().__init__()
		self.player_id = player_id
		self.server_id = server_id
		self.ordered_dids = ordered_demon_ids
		self.data_cache = {}

		# self._build_layout()

	@classmethod
	async def send(
		cls,
		destination: discord.abc.Messageable,
		*args,
		starting_demon_id: int,
		**kwargs,
	) -> discord.Message:
		"""
		Send a message wrapped in an emebd type view.

		Args:
			destination: Where to send message to.
			*args: Required arguments (see init).
			**kwargs: Keyword/optional arguments (see init).
		"""
		view = cls(*args, **kwargs)
		await view.get_demon_entries(starting_demon_id)
		return await destination.send(view=view)

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

	# def _build_layout(self) -> None:
	# 	ui = discord.ui
	# 	container = ui.Container(accent_color=self.colour)

	# 	if self.thumbnail is not None:
	# 		section = ui.Section(accessory=ui.Thumbnail(media=self.thumbnail))
	# 		section.add_item(ui.TextDisplay(self.message))
	# 		container.add_item(section)
	# 	else:
	# 		container.add_item(ui.TextDisplay(self.message))

	# 	self.add_item(container)
