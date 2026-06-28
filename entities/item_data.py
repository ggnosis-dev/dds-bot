from dataclasses import dataclass

from shared_enums import Emotes


@dataclass
class ItemEntry:
	name: str
	quantity: int
	emote: Emotes
