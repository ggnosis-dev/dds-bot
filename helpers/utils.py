import re


def get_hex_colour(hex_string: str) -> int:
	# Matches either 3 or 6 valid HEX values. Doesn't care about the #.
	match = re.search(r"^#?([0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)", hex_string)
	return int(match.group(1), 16) if match else 0
