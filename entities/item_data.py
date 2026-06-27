from dataclasses import dataclass

from shared_enums import Emotes


@dataclass
class GemEntry:
	gem: str
	quantity: int
	emote: Emotes
