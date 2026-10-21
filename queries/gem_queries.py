import random

from entities.demon_data import RaceGems
from entities.item_data import ItemEntry, convert_row_to_item_entry
from helpers.db import query_all, query_one, query_write
from queries import player_demons_queries

GEM_EXP_MULTIPLIER = 0.1
GEM_METER_FULL = 100


async def get_possible_gems(race_id: int) -> tuple[str, str]:

	rows = query_all(
		"""
			SELECT i.name FROM races r
			JOIN items i ON i.item_id IN (r.gem_1_id, r.gem_2_id)
			WHERE r.id = ?
			ORDER BY i.item_id
		""",
		(race_id,),
	)

	return tuple(row["name"] for row in rows)


async def get_gem_progress(player_id: int, demon_id: int) -> int:
	"""Get gem meter progress."""

	row = query_one(
		"""
			SELECT gem_meter FROM player_demons
			WHERE player_id = ? AND demon_id = ?
		""",
		(player_id, demon_id),
	)
	return row[0] if row else 0


async def increase_gem_meter(player_id: int, demon_id: int) -> bool:
	"""
	Add to player's gem meter and if they're over the threshold for finding a new gem, then return True.

	Args:
		demon_id (int): Player's selected demon ID to determine which gem meter to increase.
	Returns:
		bool: True if meter was full, False otherwise.
	"""

	# Get player's stored rank for demon.
	stored_rank = await player_demons_queries.get_player_demon_rank(player_id, demon_id)
	increment = stored_rank * GEM_EXP_MULTIPLIER

	# Increase meter value.
	query_write(
		"""
			UPDATE player_demons
			SET gem_meter = gem_meter + ?
			WHERE player_id = ? AND demon_id = ?
		""",
		(increment, player_id, demon_id),
	)

	meter_val = await get_gem_progress(player_id, demon_id)

	# Reset meter if gem found.
	if meter_val >= GEM_METER_FULL:
		# Remove a full meter worth of XP from the gem meter.
		query_write(
			"""
				UPDATE player_demons
				SET gem_meter = gem_meter - ?
				WHERE player_id = ? AND demon_id = ?
			""",
			(GEM_METER_FULL, player_id, demon_id),
		)

		return True
	return False


async def add_gem(player_id: int, gems: tuple[RaceGems, ...], number: int = 1) -> str:
	"""Insert or update gem quantity."""

	# Get gem type.
	gem = random.choice(gems)

	query_write(
		"""
			INSERT INTO player_gems (player_id, gem_id, quantity)
			VALUES (?, ?, ?)
			ON CONFLICT (player_id, gem_id) DO
			UPDATE SET quantity = quantity + excluded.quantity
		""",
		(player_id, gem.gem_id, number),
	)

	return gem.name


async def get_player_gems(player_id: int) -> list[ItemEntry]:
	"""
	Get a player's gem collection.

	Returns:
		list[dict]: List of gems in the player's collection. Each gem is represented as a dictionary with 'gem_name'
			and 'quantity' keys.
	"""

	rows = query_all(
		"""
			SELECT
				i.name,
				pg.quantity
			FROM player_gems pg
			JOIN items i ON pg.gem_id = i.item_id
			WHERE pg.player_id = ?
			ORDER BY i.name ASC
		""",
		(player_id,),
	)

	entries = []
	for row in rows:
		entries.append(convert_row_to_item_entry(row))
	return entries
