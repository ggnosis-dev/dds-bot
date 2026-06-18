from dataclasses import dataclass


@dataclass
class ServerStats:
	server_id: int
	level: int
	xp: int
	xp_required: int
	rank_cap: int
