from entities.badge_data import BadgeData, convert_row_to_badge_data
from helpers.db import query_all, query_one, query_write


async def get_demon_badge_id(demon_id: int) -> int | None:
	"""Get the ID of a badge."""

	result = query_one(
		"""
			SELECT id FROM badges
			WHERE demon_id = ?
		""",
		(demon_id,),
	)

	return result[0] if result else None


async def set_badge_on_player(user_id: int, badge_id: int) -> bool:
	"""Add a badge to a user (different to player)."""

	rows_affected = query_write(
		"""
			INSERT OR IGNORE INTO user_badges (user_id, badge_id)
			VALUES (?, ?)
		""",
		(user_id, badge_id),
	)
	return rows_affected > 0


async def get_all_demon_badges(user_id: int) -> list[BadgeData]:
	"""Get a list of all the badges a user has."""

	rows = query_all(
		"""
			SELECT b.id, b.emote_id, b.name
			FROM badges b
			JOIN user_badges ub ON ub.badge_id = b.id
			JOIN demons d ON d.id = b.demon_id
			WHERE ub.user_id = ?
				AND b.demon_id IS NOT NULL
			ORDER BY d.race_id ASC
		""",
		(user_id,),
	)
	return convert_row_to_badge_data(rows)
