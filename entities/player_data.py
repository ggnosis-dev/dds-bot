from dataclasses import dataclass
from sqlite3 import Row

# Hours * Seconds in an hour
DAILY_COOLDOWN = 24 * 3600
ENCOUNTER_WINDOW = 1 * 3600


@dataclass
class PartyStats:
	size: int
	comp_size: int
	cap: int
	average: int
	strongest: int


@dataclass
class PlayerData:
	player_id: int
	user_id: int
	server_id: int
	selected_demon_id: int
	mag: int
	party_stats: PartyStats
	daily_timer: int
	encounter_timer: int


def convert_row_to_player_data(row: Row, party_stats: PartyStats) -> PlayerData:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		return PlayerData(
			player_id=row["player_id"],
			user_id=row["user_id"],
			server_id=row["server_id"],
			selected_demon_id=row["selected_demon_id"],
			mag=row["mag"],
			party_stats=party_stats,
			daily_timer=row["daily_timer"],
			encounter_timer=row["encounter_timer"],
		)
	except Exception as e:
		print(e)
		raise KeyError(f"ERROR: Problem when creating PlayerData | {e}")
