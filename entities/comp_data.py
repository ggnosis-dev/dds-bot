from dataclasses import dataclass


@dataclass
class ServerCompendiumDemon:
	"""Thin data class used for operations."""

	server_id: int
	player_id: int
	demon_id: int
	stored_rank: int


@dataclass
class DemonEntry:
	"""For view/displaying player demons."""

	demon_id: int
	name: str
	race: str
	on_loan: bool = False
	stored_rank: int = 0
	# For player demon only.
	in_party: bool | None = None
	# For server demon only.
	owner_id: int | None = None
	owner: str | None = None

	@property
	def is_unseen(self) -> bool:
		return self.in_party is None and self.owner_id is None
