from dataclasses import dataclass
from sqlite3 import Row

DAILY_COOLDOWN = 43200 * 2
ENCOUNTER_WINDOW = 1 * 3600


@dataclass
class PartyStats:
	size: int
	cap: int
	average: int
	strongest: int


@dataclass
class PlayerData:
	player_id: int
	server_id: int
	selected_demon_id: int
	mag: int
	party_stats: PartyStats
	daily_timer: int
	encounter_timer: int


def convert_row_to_player_data(row: Row, strongest: int) -> PlayerData:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		return PlayerData(
			player_id=row["player_id"],
			server_id=row["server_id"],
			selected_demon_id=row["selected_demon_id"],
			mag=row["mag"],
			party_stats=PartyStats(
				size=row["party_size"],
				cap=row["party_cap"],
				average=row["party_average_rank"],
				strongest=strongest,
			),
			daily_timer=row["daily_timer"],
			encounter_timer=row["encounter_timer"],
		)
	except Exception as e:
		print(e)
		raise KeyError(f"ERROR: Problem when creating PlayerData | {e}")
