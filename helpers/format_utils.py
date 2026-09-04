import re

from entities.demon_data import DemonData
from shared_enums import Emotes

EVIL_PATTERNS = [
	re.compile(r"@everyone", re.IGNORECASE),
	re.compile(r"@here", re.IGNORECASE),
	re.compile(r"@game", re.IGNORECASE),
	re.compile(r"@time", re.IGNORECASE),
	# User and Role mentions.
	re.compile(r"<@!?&?\d+>", re.IGNORECASE),
	# Zero width space and bidirectional text.
	re.compile(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]"),
	# Control characters.
	re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]"),
]


def format_dialogue(message: str, demon_data: DemonData) -> str:
	if not message.startswith("[p]"):
		message = f"-# {message}"
	else:
		message.replace("[p]", "", 1)

	message = message.replace("[p]", "\n\n")
	message = message.replace("[d]", "\n\n-# ")
	message = message.replace("[race]", f"{demon_data.race.upper()}")
	message = message.replace("[name]", f"{demon_data.name.upper()}")
	message = message.replace("[gem]", f"{demon_data.gems[0]}")

	return message


def format_greeting(message: str, demon_data: DemonData) -> str:
	message = message.replace("[r]", f"{demon_data.race}")
	message = message.replace("[R]", f"{demon_data.race.upper()}")
	message = message.replace("[d]", f"{demon_data.name}")
	message = message.replace("[D]", f"{demon_data.name.upper()}")

	message = message.replace("[s]", f"{demon_data.dupes}{Emotes.GEM_THIN.value}")
	message = message.replace("[k]", f"{demon_data.rank}")
	message = message.replace("[g1]", f"{demon_data.gems[0].title()}")
	message = message.replace("[g2]", f"{demon_data.gems[1].title()}")
	return message


def sanitise_input(message: str, max_length: int) -> str | None:
	# None if too long.
	if len(message) > max_length:
		return None

	# Check for annoying patterns that we don't want storing/displaying.
	for pattern in EVIL_PATTERNS:
		if pattern.search(message):
			return None

	return message
