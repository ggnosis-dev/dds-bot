from dataclasses import dataclass

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
class DemonEntry:
	"""For view/displaying player demons."""

	demon_id: int
	name: str
	race: str
	initial_rank: int = 0
	stored_rank: int = 0
	gems: tuple | None = None
	tone_name: str | None = None
	on_loan: bool = False
	# For player demon only.
	in_party: bool | None = None
	# For server demon only.
	owner_id: int | None = None
	owner_name: str | None = None

	@property
	def is_unseen(self) -> bool:
		return self.in_party is None and self.owner_id is None


def convert_row_to_demon_entry(rows: list, need_gems: bool) -> list[DemonEntry]:
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
		gem_cache: dict[str, tuple] = {}

		for row in rows:
			row = dict(row)
			st_rank = row.get("stored_rank")
			gems = None

			# If we're querying gems, make sure to skip anything that's not seen.
			if need_gems and st_rank is not None:
				race = row["race"]

				if race not in gem_cache:
					gem_cache[race] = get_possible_gems(race)
				gems = gem_cache[race]

			entries.append(
				DemonEntry(
					demon_id=row["id"],
					name=row["name"],
					race=row["race"],
					initial_rank=row["rank"],
					stored_rank=st_rank or 0,
					gems=gems,
					tone_name=Tone(row["tone"]).name,
					on_loan=row.get("on_loan", False),
					in_party=row.get("in_party"),
					owner_id=row.get("owner_id"),
				)
			)

		return entries
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating DemonEntry | {e}")
