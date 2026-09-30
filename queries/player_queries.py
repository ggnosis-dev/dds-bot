import asyncio

from time import time

from entities.demon_data import DEFAULT_RACE_MULT_INCREMENT
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
	if await check_player_exists(player_id, server_id):
		return False

	await asyncio.gather(
		save_player_to_db(player_id, server_id),
		update_server_in_db(server_id),
	)

	return True


async def save_player_to_db(player_id: int, server_id: int) -> bool:
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


async def check_player_exists(player_id, server_id) -> bool:
	"""
	Check if a player already exists in the database.

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
		PlayerData: A data class of player properties or None if non-existent.
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


async def set_daily_timer(player_id: int, server_id: int) -> bool:
	"""Set the player's daily timer."""
	time_now = int(time())

	rows_affected = query_write(
		"""
			UPDATE players
			SET daily_timer = ?
			WHERE player_id = ? AND server_id = ?
		""",
		(time_now, player_id, server_id),
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


async def increase_race_mag_mult(
	player_id: int,
	server_id: int,
	race_id: int,
	amount: float = DEFAULT_RACE_MULT_INCREMENT,
) -> float:
	response = query_one(
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
			RETURNING mag_mult
		""",
		(player_id, server_id, race_id, amount),
	)

	return response[0]


async def get_race_mag_mult(player_id: int, server_id: int, race_id: int) -> float:
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


# ----- TUTORIAL ----- #
async def check_tutorial_complete(player_id, server_id) -> bool:
	"""
	Check if a player has completed the tutorial.

	Returns:
		bool: True if player finished tutorial, False otherwise.
	"""
	response = query_one(
		"""
			SELECT tutorial_complete FROM players
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	return response[0] if response else False


async def get_tutorial_progress(player_id, server_id) -> tuple:
	"""
	Get step and task_mask, signifying tutorial progress.

	Returns:
		bool: True if player finished tutorial, False otherwise.
	"""
	response = query_one(
		"""
			SELECT step, task_mask FROM tutorial
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	if response is not None:
		return response[0], response[1]
	else:
		return (1, 0)


async def set_tutorial_mask(player_id: int, server_id: int, mask: int) -> bool:
	# Might need to add entry first.
	rows_affected = query_write(
		"""
			INSERT INTO tutorial (player_id, server_id, step, task_mask)
			VALUES (?, ?, 1, ?)
			ON CONFLICT (player_id, server_id) DO
				UPDATE SET task_mask = ?
		""",
		(player_id, server_id, mask, mask),
	)

	return rows_affected > 0


async def next_tutorial_step(player_id: int, server_id: int) -> bool:
	rows_affected = query_write(
		"""
			UPDATE tutorial
			SET step = step + 1, task_mask = 0
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	return rows_affected > 0
