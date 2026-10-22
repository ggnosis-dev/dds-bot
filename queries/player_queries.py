from time import time

from entities.demon_data import DEFAULT_RACE_MULT_INCREMENT
from entities.player_data import PartyStats, PlayerData, convert_row_to_player_data
from helpers.db import query_one, query_write
from queries.server_queries import update_server_in_db


async def setup_player(user_id, server_id) -> bool:
	"""
	Set up a new player in the database if they don't already have a profile.

	Returns:
		bool: True if a new profile was created, False if player already exists.
	"""
	query_write(
		"""
			INSERT INTO servers (server_id)
			VALUES (?)
			ON CONFLICT DO NOTHING
		""",
		(server_id,),
	)

	rows = query_write(
		"""
			INSERT INTO players (user_id, server_id)
			VALUES (?, ?)
			ON CONFLICT (user_id, server_id) DO NOTHING
		""",
		(user_id, server_id),
	)

	if rows > 0:
		print(f"INFO: New player added. User {user_id} | Server {server_id}.")
		await update_server_in_db(server_id)

	return rows > 0


async def get_player_id(user_id: int, server_id: int) -> int | None:
	row = query_one(
		"""
			SELECT player_id
			FROM players
			WHERE user_id = ? AND server_id = ?
		""",
		(user_id, server_id),
	)
	return row[0] if row else None


async def check_player_exists(user_id: int, server_id: int) -> bool:
	"""Check if a player already exists in the database."""
	return await get_player_id(user_id, server_id) is not None


async def get_player(player_id: int) -> PlayerData:
	"""
	Get the properties of the player.

	Returns:
		PlayerData: A data class of player properties or None if non-existent.
	"""
	row = query_one(
		"""
			SELECT * FROM players
			WHERE player_id = ?
		""",
		(player_id,),
	)

	# Get party stats.
	party_stats = await get_party_stats(player_id)
	return convert_row_to_player_data(row, party_stats)


async def get_party_stats(player_id: int) -> PartyStats:
	row = query_one(
		"""
			SELECT party_size, comp_size, party_average_rank, party_cap, strongest_rank
			FROM player_party_stats_VIEW
			WHERE player_id = ?
		""",
		(player_id,),
	)

	return PartyStats(
		size=row["party_size"],
		comp_size=row["comp_size"],
		cap=row["party_cap"],
		average=row["party_average_rank"],
		strongest=row["strongest_rank"],
	)


def get_party_has_space(player_id: int) -> bool:
	"""Check if the player's party is full."""

	row = query_one(
		"""
			SELECT 1 FROM player_party_stats_VIEW
			WHERE party_size < party_cap
				AND player_id = ?
		""",
		(player_id,),
	)
	return row is not None


async def set_daily_timer(player_id: int) -> bool:
	"""Set the player's daily timer."""
	time_now = int(time())

	rows_affected = query_write(
		"""
			UPDATE players
			SET daily_timer = ?
			WHERE player_id = ?
		""",
		(time_now, player_id),
	)
	return rows_affected > 0


async def set_encounter_timer(player_id: int, time: int) -> bool:
	"""Set the player's encounter timer."""
	rows_affected = query_write(
		"""
			UPDATE players
			SET encounter_timer = ?
			WHERE player_id = ?
		""",
		(time, player_id),
	)
	return rows_affected > 0


async def increase_party_slots(player_id: int, number: int) -> bool:
	"""Add however many slots to the player's party."""
	rows_affected = query_write(
		"""
			UPDATE players
			SET party_cap = party_cap + ?
			WHERE player_id = ?
		""",
		(number, player_id),
	)
	return rows_affected > 0


async def increase_race_mag_mult(
	player_id: int,
	race_id: int,
	amount: float = DEFAULT_RACE_MULT_INCREMENT,
) -> float:
	"""Add to player's race specific MAG multiplier."""
	row = query_one(
		"""
			INSERT INTO player_race_stats (
				player_id,
				race_id,
				mag_mult
			)
			VALUES (?, ?, 1.1)
			ON CONFLICT (player_id, race_id) DO
				UPDATE SET mag_mult = mag_mult + ?
			RETURNING mag_mult
		""",
		(player_id, race_id, amount),
	)
	return row[0]


async def get_race_mag_mult(player_id: int, race_id: int) -> float:
	"""Get the value to mutliply MAG by for the player."""
	row = query_one(
		"""
		SELECT mag_mult FROM player_race_stats
		WHERE player_id = ? AND race_id = ?
		""",
		(player_id, race_id),
	)
	return row[0] if row is not None else 1


# ----- TUTORIAL ----- #
async def check_tutorial_complete(player_id: int) -> bool:
	"""Check if a player has completed the tutorial."""
	row = query_one(
		"""
			SELECT tutorial_complete FROM players
			WHERE player_id = ?
		""",
		(player_id,),
	)
	return row[0] if row else False


async def get_tutorial_progress(player_id: int | None) -> tuple:
	"""Get step and task_mask, signifying tutorial progress."""
	if player_id is None:
		return (1, 0)

	row = query_one(
		"""
			SELECT step, task_mask FROM tutorial
			WHERE player_id = ?
		""",
		(player_id,),
	)
	return (row[0], row[1]) if row else (1, 0)


async def set_tutorial_mask(player_id: int, mask: int) -> bool:
	"""Set the player's bitmask for the tutorial tasks."""
	# Might need to add entry first.
	rows_affected = query_write(
		"""
			INSERT INTO tutorial (player_id, step, task_mask)
			VALUES (?, 1, ?)
			ON CONFLICT (player_id) DO
				UPDATE SET task_mask = ?
		""",
		(player_id, mask, mask),
	)
	return rows_affected > 0


async def next_tutorial_step(player_id: int) -> bool:
	"""Update player's step and reset task bitmask."""
	rows_affected = query_write(
		"""
			UPDATE tutorial
			SET step = step + 1, task_mask = 0
			WHERE player_id = ?
		""",
		(player_id,),
	)
	return rows_affected > 0
