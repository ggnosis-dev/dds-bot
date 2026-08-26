from dataclasses import dataclass


@dataclass
class BadgeData:
	"""Thin data class used for operations."""

	badge_id: int
	emote_id: int
	name: str


def convert_row_to_badge_data(rows: list) -> list[BadgeData]:
	"""Convert retrieved DB row into list of BadgeData objects."""
	try:
		entries = []

		for row in rows:
			entries.append(
				BadgeData(
					badge_id=row["id"],
					emote_id=row["emote_id"],
					name=row["name"],
				)
			)

		return entries
	except Exception as e:
		raise KeyError(f"Problem when creating BadgeData | {e}")
