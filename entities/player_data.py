from dataclasses import dataclass


@dataclass
class PlayerData:
	player_id: int
	server_id: int
	selected_demon_id: int
	mag: int
	daily_timer: int
