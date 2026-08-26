from dataclasses import dataclass

from shared_enums import Emotes


@dataclass
class ItemEntry:
	name: str
	quantity: int
	emote: Emotes
	description: str


@dataclass
class ItemData:
	item_id: int
	name: str
	i_type: str
	cost: dict
	description: str
	emote: str
	exclusive_to: str
