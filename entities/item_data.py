from dataclasses import astuple, dataclass

from shared_enums import Emotes


@dataclass
class ItemEntry:
	name: str
	quantity: int
	emote: Emotes


@dataclass
class ItemData:
	name_id: str
	display_name: str
	description: str
	cost: tuple[str, int]
	emote: Emotes
	exclusive_to: str

	def __iter__(self):
		"""Establish an iterator so we can... well iterate through stuff."""
		return iter(astuple(self))
