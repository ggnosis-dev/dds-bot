from helpers.db import query_all, query_one, query_write

GEM_EXP_MULTIPLIER = 1
GEM_METER_FULL = 100


async def increase_gems(player_id: int, server_id: int, demon_id: int) -> bool:
	"""
	Add to player's gem meter and add a gem to their count if over a threshold.
	Return whether a gem has been found.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
		demon_id (int): Player's selected demon ID to determine which gem meter to increase.
	Returns:
		bool: True if gem was found, False otherwise.
	"""
	# Get gem type and the player's stored rank for demon.
	gem_name, stored_rank = query_one(
		"""
			SELECT d.gem, pd.stored_rank FROM demons d
			JOIN player_demons pd ON pd.demon_id = d.id
			WHERE d.id = ?
		""",
		(demon_id,),
	)

	increment = stored_rank * GEM_EXP_MULTIPLIER

	# Increase gem meter, returning meter value. excluded.meter is the value that was going to be insert into the meter.
	meter_val = query_one(
		"""
			INSERT INTO player_gems (player_id, server_id, gem_name, meter, quantity)
			VALUES (?, ?, ?, ?, 0)
			ON CONFLICT (player_id, server_id, gem_name) DO
			UPDATE SET meter = meter + excluded.meter
			RETURNING meter
		""",
		(player_id, server_id, gem_name, increment),
	)[0]

	# Add gem to count and reset meter if gem found.
	if meter_val >= GEM_METER_FULL:
		query_write(
			"""
				UPDATE player_gems
				SET meter = 0, quantity = quantity + 1
				WHERE player_id = ? AND server_id = ? AND gem_name = ?
			""",
			(player_id, server_id, gem_name),
		)

		return True
	return False


async def add_gem(player_id: int, server_id: int, demon_id: int, number: int) -> None:
	# Get gem type.
	gem_name = query_one(
		"""
			SELECT d.gem FROM demons d
			JOIN player_demons pd ON pd.demon_id = d.id
			WHERE d.id = ?
		""",
		(demon_id,),
	)[0]

	query_write(
		"""
			INSERT INTO player_gems (player_id, server_id, gem_name, meter, quantity)
			VALUES (?, ?, ?, 0, ?)
			ON CONFLICT (player_id, server_id, gem_name) DO
			UPDATE SET quantity = quantity + ?
		""",
		(player_id, server_id, gem_name, number, number),
	)


def get_player_gems(player_id: int, server_id: int) -> list[dict]:
	"""
	Get a player's gem collection.

	Returns:
		list[dict]: List of gems in the player's collection. Each gem is represented as a dictionary with 'gem_name'
			and 'quantity' keys.
	"""
	result = query_all(
		"""
			SELECT gem_name, quantity FROM player_gems
			WHERE player_id = ? AND server_id = ?
			ORDER BY gem_name ASC
		""",
		(player_id, server_id),
	)

	return result if result else []


def get_gem_progress(player_id: int, server_id: int, gem_name: str) -> int:
	"""Get gem meter progress."""
	result = query_one(
		"""
			SELECT meter FROM player_gems
			WHERE player_id = ? AND server_id = ? AND gem_name = ?
		""",
		(player_id, server_id, gem_name),
	)

	return result[0] if result else 0
