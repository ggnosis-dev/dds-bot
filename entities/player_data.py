from dataclasses import dataclass


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
