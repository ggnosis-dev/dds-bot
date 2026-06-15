from dataclasses import dataclass


@dataclass
class PlayerData:
	player_id: int
	server_id: int
	mag: int
	selected_demon_id: int
	daily_timer: int
