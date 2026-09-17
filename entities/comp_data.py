from dataclasses import dataclass
from sqlite3 import Row

from entities.demon_data import DesignData, convert_row_to_design_data
from queries.gem_queries import get_possible_gems
from shared_enums import Tone


@dataclass
class ServerCompendiumDemon:
	"""Thin data class used for operations."""

	server_id: int
	player_id: int
	demon_id: int
	stored_rank: int


@dataclass
class DemonTableRow:
	"""For view/displaying player demons in a table format."""

	demon_id: int
	name: str
	race: str
	stored_rank: int
	# Potential columns.
	initial_rank: int = 0
	dupes: int = 0
	tone_name: str | None = None
	gems: tuple[str, str] | None = None
	on_loan: bool = False
	# For player demon only.
	in_party: bool | None = None
	# For server demon only.
	owner_id: int | None = None
	owner_name: str | None = None

	@property
	def is_unseen(self) -> bool:
		return self.in_party is None and self.owner_id is None


@dataclass
class DemonEntry:
	"""For viewing registered demons in the :class:`DemonEntryBrowser` view."""

	demon_id: int
	name: str
	race: str
	initial_rank: int
	stored_rank: int
	dupes: int
	tone_name: str
	gems: tuple[str, str]
	design_data: DesignData
	date_met: int
	desc: str | None
	origin: str | None


def convert_row_to_demon_entry(row: Row) -> DemonEntry:
	try:
		row_keys = row.keys()
		desc = row["desc"] if "desc" in row_keys else None
		origin = row["origin"] if "origin" in row_keys else None

		return DemonEntry(
			demon_id=row["id"],
			name=row["name"],
			race=row["race"].title(),
			initial_rank=row["rank"],
			stored_rank=row["stored_rank"],
			dupes=row["dupes"],
			tone_name=Tone(row["tone"]).name,
			gems=(row["gem_1"], row["gem_2"]),
			design_data=convert_row_to_design_data(row),
			date_met=row["date_met"],
			desc=desc,
			origin=origin,
		)
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating DemonEntry | {e}")


async def convert_row_to_demon_table_rows(rows: list[Row], need_gems: bool) -> list[DemonTableRow]:
	"""
	Convert retrieved DB rows into list of DemonEntry.

	Args:
		rows (list): A list containing demon entry data.
		need_gems (bool): If true, get race's gems.
	Returns:
		list[DemonEntry]: Normalised list of DemonEntry created from values provided.
	"""
	try:
		entries = []
		# { race_id: (GEM, NAMES) }
		gem_cache: dict[int, tuple[str, str]] = {}

		for raw_row in rows:
			row: dict = dict(raw_row)
			st_rank = row.get("stored_rank", 0)
			gems = None

			# If we're querying gems, make sure to skip anything that's not seen.
			if need_gems and st_rank is not None:
				race_id = row["race_id"]

				# Skip retrieving gems if they're already in the cache.
				if race_id not in gem_cache:
					gem_cache[race_id] = await get_possible_gems(race_id)
				gems = gem_cache[race_id]

			row["stored_rank"] = st_rank
			row["gems"] = gems
			entries.append(convert_row_to_demon_table_row(row))

		return entries
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating DemonEntry | {e}")


def convert_row_to_demon_table_row(raw_row: Row | dict) -> DemonTableRow:
	try:
		row = dict(raw_row)

		return DemonTableRow(
			demon_id=row["id"],
			name=row["name"],
			race=row["race"].title(),
			initial_rank=row["rank"],
			stored_rank=row["stored_rank"],
			dupes=row.get("dupes", 0),
			gems=row.get("gems"),
			tone_name=Tone(row["tone"]).name,
			on_loan=row.get("on_loan", False),
			in_party=row.get("in_party"),
			owner_id=row.get("owner_id"),
		)
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating DemonEntry | {e}")
