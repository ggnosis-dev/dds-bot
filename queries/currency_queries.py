from helpers.database import query_count, query_one


def get_mag(player_id: int, server_id: int) -> int:
	"""Get the amount of magnetite a player has."""
	result = query_one(
		"""
		SELECT mag FROM players
		WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)
	return result[0] if result else 0


def update_mag(player_id: int, server_id: int, amount: int) -> bool:
	"""Update the amount of magnetite a player has."""
	rows_affected = query_count(
		"""
		UPDATE players
		SET mag = mag + ?
		WHERE player_id = ? AND server_id = ?
		""",
		(amount, player_id, server_id),
	)

	return rows_affected > 0
