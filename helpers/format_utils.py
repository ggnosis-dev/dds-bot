import re

from entities.demon_data import GREETING_LENGTH, DemonData
from queries.gem_queries import get_possible_gems
from shared_enums import Emotes

EVIL_PATTERNS = [
	r"@everyone",
	r"@here",
	r"@game",
	r"@time",
	# User and Role mentions.
	r"<@!?&?\d+>",
	# Zero-width & bidi override characters.
	r"[\u200b-\u200f\u202a-\u202e]",
	# Control characters.
	r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
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

	if "[gem]" in message:
		gems = get_possible_gems(demon_data.race)
		message = message.replace("[gem]", f"{gems[0]}")

	return message


def format_greeting(message: str, demon_data: DemonData) -> str:
	message = message.replace("[r]", f"{demon_data.race}")
	message = message.replace("[R]", f"{demon_data.race.upper()}")
	message = message.replace("[d]", f"{demon_data.name}")
	message = message.replace("[D]", f"{demon_data.name.upper()}")
	message = message.replace("[s]", f"{demon_data.dupes}{Emotes.GEM_THIN.value}")
	message = message.replace("[r]", f"{demon_data.rank}")
	return message


def sanitise_greeting(message: str) -> str | None:
	# None if too long.
	if len(message) > GREETING_LENGTH:
		return None

	# Check for annoying patterns that we don't want storing.
	for pattern in EVIL_PATTERNS:
		if re.search(pattern, message, re.IGNORECASE):
			return None

	return message
