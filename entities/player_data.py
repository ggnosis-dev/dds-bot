from dataclasses import dataclass


@dataclass
class PlayerData:
	player_id: int
	server_id: int
	selected_demon_id: int
	mag: int
	party_size: int
	party_cap: int
	party_average_rank: int
	daily_timer: int
	encounter_timer: int
