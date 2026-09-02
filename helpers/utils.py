import re

from time import time

from entities.command_data import INPUT_DIVIDER


def get_hex_colour(hex_string: str) -> int:
	# Matches either 3 or 6 valid HEX values. Doesn't care about the #.
	match = re.search(r"^#?([0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)", hex_string)
	return int(match.group(1), 16) if match else 0


def split_input_str(input_str: str | None, maximum: int = 2) -> tuple[str, ...]:
	if input_str is None:
		return ()

	parts = input_str.split(INPUT_DIVIDER, maximum)

	# Don't loop through everything because we'll just be throwing it out.
	parts_limit = min(len(parts), maximum)
	for i in range(parts_limit):
		parts[i] = parts[i].strip().title()
	return tuple(parts)


def get_time_until(timer: int, duration: int) -> tuple[int, ...] | None:
	time_now = int(time())
	time_since = time_now - timer

	# If still time, return how much time is left.
	if time_since < duration:
		remaining = duration - time_since
		hours, remainder = divmod(remaining, 3600)
		minutes, seconds = divmod(remainder, 60)
		return hours, minutes, seconds
	return None
