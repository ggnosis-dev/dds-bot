from dataclasses import dataclass


@dataclass
class ServerStats:
	server_id: int
	level: int
	current_level_xp: int
	xp_required: int
	rank_cap: int
	total_xp: int
