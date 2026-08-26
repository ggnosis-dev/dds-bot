from entities.badge_data import BadgeData, convert_row_to_badge_data
from helpers.db import query_all, query_one, query_write


def get_demon_badge_id(demon_id: int) -> int | None:
	"""Get the amount of magnetite a player has."""
	result = query_one(
		"""
			SELECT id FROM badges b
			WHERE demon_id = ?
		""",
		(demon_id,),
	)

	return result[0] if result else None


def set_badge_on_player(player_id: int, badge_id: int) -> bool:
	"""Update the amount of magnetite a player has."""
	rows_affected = query_write(
		"""
			INSERT OR IGNORE INTO player_badges (player_id, badge_id)
			VALUES (?, ?)
		""",
		(player_id, badge_id),
	)

	return rows_affected > 0


def get_all_demon_badges(player_id: int) -> list[BadgeData]:
	"""Get the amount of magnetite a player has."""
	rows = query_all(
		"""
			SELECT b.id, b.emote_id, b.name
			FROM badges b
			JOIN player_badges pb ON pb.badge_id = b.id
			JOIN demons d ON d.id = b.demon_id
			WHERE pb.player_id = ?
				AND b.demon_id IS NOT NULL
			ORDER BY d.race_id ASC
		""",
		(player_id,),
	)

	return convert_row_to_badge_data(rows)
