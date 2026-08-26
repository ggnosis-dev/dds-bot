from entities.player_data import PlayerData, convert_row_to_player_data
from helpers.db import query_one, query_write
from queries.player_demons_queries import get_strongest_party_demon_rank
from queries.server_queries import update_server_in_db


async def setup_player(player_id, server_id) -> bool:
	"""
	Set up a new player in the database if they don't already have a profile.

	Returns:
		bool: True if a new profile was created, False if player already exists.
	"""
	if check_player_exists(player_id, server_id):
		return False

	save_player_to_db(player_id, server_id)
	update_server_in_db(server_id)

	return True


def save_player_to_db(player_id: int, server_id: int) -> bool:
	"""Save a new player's data to the database."""
	rows_affected = query_write(
		"""
			INSERT INTO players (player_id, server_id)
				VALUES (?, ?)
		""",
		(player_id, server_id),
	)
	print(f"INFO: New player added: {player_id} | Server {server_id}.")
	return rows_affected > 0


def check_player_exists(player_id, server_id) -> bool:
	"""
	Check if a player already exists in the database.

	Args:
		player_id (int): Player ID.
		player_server (int): Server ID the player belongs to.
	Returns:
		bool: True if the player exists, False otherwise.
	"""
	response = query_one(
		"""
			SELECT 1 FROM players
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	return response is not None


async def get_player(player_id, server_id) -> PlayerData | None:
	"""
	Get the properties of the player.
	Returns:
		PlayerData | None: A data class of player properties or None if non-existent.
	"""

	row = query_one(
		"""
			SELECT * FROM players
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	if row is None:
		return None

	strongest = await get_strongest_party_demon_rank(player_id, server_id)
	return convert_row_to_player_data(row, strongest)


async def set_daily_timer(player_id: int, server_id: int, time: int) -> bool:
	"""
	Set the player's daily timer.

	Returns:
		bool: True if successful, False otherwise.
	"""
	rows_affected = query_write(
		"""
			UPDATE players
			SET daily_timer = ?
			WHERE player_id = ? AND server_id = ?
		""",
		(time, player_id, server_id),
	)

	return rows_affected > 0


async def set_encounter_timer(player_id: int, server_id: int, time: int) -> bool:
	"""
	Set the player's encounter timer.

	Returns:
		bool: True if successful, False otherwise.
	"""
	rows_affected = query_write(
		"""
			UPDATE players
			SET encounter_timer = ?
			WHERE player_id = ? AND server_id = ?
		""",
		(time, player_id, server_id),
	)

	return rows_affected > 0


async def increase_party_slots(player_id: int, server_id: int, number: int) -> bool:
	rows_affected = query_write(
		"""
			UPDATE players
			SET party_cap = party_cap + ?
			WHERE player_id = ? AND server_id = ?
		""",
		(number, player_id, server_id),
	)

	return rows_affected > 0


async def increase_race_mag_mult(player_id: int, server_id: int, race_id: int, amount: float = 0.1) -> bool:
	rows_affected = query_write(
		"""
			INSERT INTO player_race_stats (
				player_id,
				server_id,
				race_id,
				mag_mult
			)
			VALUES (?, ?, ?, 1.1)
			ON CONFLICT (player_id, server_id, race_id) DO
				UPDATE SET mag_mult = mag_mult + ?
		""",
		(player_id, server_id, race_id, amount),
	)

	return rows_affected > 0


def get_race_mag_mult(player_id: int, server_id: int, race_id: int) -> float:
	response = query_one(
		"""
		SELECT mag_mult FROM player_race_stats
		WHERE player_id = ?
			AND server_id = ?
			AND race_id = ?
		""",
		(player_id, server_id, race_id),
	)

	return response[0] if response is not None else 1
