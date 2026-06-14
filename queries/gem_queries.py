import sqlite3

from database_paths import PLAYERS_DB_PATH

GEM_EXP_MULTIPLIER = 1
GEM_METER_FULL = 100


def _get_db_connection() -> sqlite3.Connection:
	"""Helper method to get a connection to the players database."""
	conn = sqlite3.connect(PLAYERS_DB_PATH)

	# Enforce foreign key constraints for the connection.
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


async def increase_gems(player_id: int, server_id: int, demon_id: int) -> bool:
	"""
	Add to player's gem meter and add a gem to their count if over a threshold.
	Return whether a gem has been found.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
		selected_demon_id (int): Player's selected demon ID to determine which gem meter to increase.
		exp (int): Amount to increase the gem meter by.
	Returns:
		bool: True if gem was found, False otherwise.
	"""
	with _get_db_connection() as conn:
		cursor = conn.cursor()

		# Get gem type and the player's stored rank for demon.
		gem_name, stored_rank = cursor.execute(
			"""
			SELECT d.gem, pd.stored_rank FROM demons d
			JOIN player_demons pd ON pd.demon_id = d.id
			WHERE d.id = ?
			""",
			(demon_id,),
		).fetchone()

		if gem_name is None:
			return False

		stored_rank = stored_rank * GEM_EXP_MULTIPLIER

		# Increase gem meter by exp, returning meter value. excluded.meter is the value that was going to be insert
		# into the meter.
		cursor.execute(
			"""
			INSERT INTO player_gems (player_id, server_id, gem_name, meter, quantity)
			VALUES (?, ?, ?, ?, 0)
			ON CONFLICT (player_id, server_id, gem_name) DO
			UPDATE SET meter = meter + excluded.meter
			RETURNING meter
			""",
			(player_id, server_id, gem_name, stored_rank),
		)

		# Get the meter value after the update to check if a gem has been found.
		meter_val = cursor.fetchone()[0]
		print(f"DEBUG: Player {player_id} | Server {server_id} | Gem {gem_name} meter: {meter_val:.2f}")

		# Add gem to count and reset meter if gem found.
		if meter_val >= GEM_METER_FULL:
			cursor.execute(
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
	with _get_db_connection() as conn:
		cursor = conn.cursor()

		# Get gem type.
		(gem_name,) = cursor.execute(
			"""
			SELECT d.gem FROM demons d
			JOIN player_demons pd ON pd.demon_id = d.id
			WHERE d.id = ?
			""",
			(demon_id,),
		).fetchone()

		print(f"DEBUG: Player {player_id} | Server {server_id} | Gem {gem_name} | Number: {number}")

		cursor.execute(
			"""
			INSERT INTO player_gems (player_id, server_id, gem_name, meter, quantity)
			VALUES (?, ?, ?, 0, ?)
			ON CONFLICT (player_id, server_id, gem_name) DO
			UPDATE SET quantity = quantity + ?
			""",
			(player_id, server_id, gem_name, number, number),
		)


def get_player_gems(player_id: int, server_id: int) -> list[tuple]:
	"""
	Get a player's gem collection.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
	Returns:
		list[dict]: List of gems in the player's collection. Each gem is represented as a dictionary with 'gem_name'
			and 'quantity' keys.
	"""
	with _get_db_connection() as conn:
		cursor = conn.cursor()
		result = cursor.execute(
			"""
			SELECT gem_name, quantity FROM player_gems
			WHERE player_id = ? AND server_id = ?
			ORDER BY gem_name ASC
			""",
			(player_id, server_id),
		).fetchall()

		return result if result else []


def get_gem_progress(player_id: int, server_id: int, gem_name: str) -> int:
	"""Get gem meter progress."""
	with _get_db_connection() as conn:
		cursor = conn.cursor()
		result = cursor.execute(
			"""
			SELECT meter FROM player_gems
			WHERE player_id = ? AND server_id = ? AND gem_name = ?
			""",
			(player_id, server_id, gem_name),
		).fetchone()

		return result[0] if result else 0
