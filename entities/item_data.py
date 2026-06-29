from dataclasses import dataclass

from shared_enums import Emotes


@dataclass
class ItemEntry:
	name: str
	quantity: int
	emote: Emotes


@dataclass
class ItemData:
	item_id: str
	name: str
	i_type: str
	cost: dict
	description: str
	emote: str
	exclusive_to: str
