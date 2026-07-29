from dataclasses import dataclass

DAILY_COOLDOWN = 43200 * 2
ENCOUNTER_WINDOW_HOURS = 3


@dataclass
class PartyStats:
	size: int
	cap: int
	average: int


@dataclass
class PlayerData:
	player_id: int
	server_id: int
	selected_demon_id: int
	mag: int
	party_stats: PartyStats
	daily_timer: int
	encounter_timer: int
	faction_id: int
