from dataclasses import dataclass


@dataclass
class ServerCompendiumDemon:
	"""Thin data class used for operations."""

	player_id: int
	server_id: int
	demon_id: int
	stored_rank: int


@dataclass
class DemonEntry:
	"""For view/displaying player demons."""

	demon_id: int
	name: str
	race: str
	personality: str
	rank: int | None
	gem: str
	# For player demon only.
	in_party: bool | None = None
	# For server demon only.
	owner_id: int | None = None
	owner: str | None = None
