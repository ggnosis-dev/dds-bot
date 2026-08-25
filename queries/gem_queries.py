import random

from entities.item_data import ItemEntry
from helpers.db import query_all, query_one, query_write
from queries import player_demons_queries
from shared_enums import Emotes

GEM_EXP_MULTIPLIER = 1
GEM_METER_FULL = 100


def get_possible_gems(race: str) -> tuple:
	response = query_all(
		"""
			SELECT gem_1, gem_2 FROM races
			WHERE name = UPPER(?)
		""",
		(race,),
	)

	return tuple(response[0])


async def increase_gem_meter(player_id: int, server_id: int, demon_id: int) -> bool:
	"""
	Add to player's gem meter and if they're over the threshold for finding a new gem, then return True.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
		demon_id (int): Player's selected demon ID to determine which gem meter to increase.
	Returns:
		bool: True if meter was full, False otherwise.
	"""

	# Get player's stored rank for demon.
	stored_rank = await player_demons_queries.get_player_demon_rank(player_id, server_id, demon_id)
	increment = stored_rank * GEM_EXP_MULTIPLIER

	# Increase meter value.
	query_write(
		"""
			UPDATE player_demons
			SET gem_meter = gem_meter + ?
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(increment, player_id, server_id, demon_id),
	)

	meter_val = get_gem_progress(player_id, server_id, demon_id)

	# Reset meter if gem found.
	if meter_val >= GEM_METER_FULL:
		# Remove a full meter worth of XP from the gem meter.
		query_write(
			"""
				UPDATE player_demons
				SET gem_meter = gem_meter - ?
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			""",
			(GEM_METER_FULL, player_id, server_id, demon_id),
		)

		return True
	return False


async def add_gem(player_id: int, server_id: int, race: str, number: int = 1) -> str:
	# Get gem type.
	gems = get_possible_gems(race)
	gem_name = random.choice(gems)

	query_write(
		"""
			INSERT INTO player_gems (player_id, server_id, gem_name, quantity)
			VALUES (?, ?, ?, ?)
			ON CONFLICT (player_id, server_id, gem_name) DO
			UPDATE SET quantity = quantity + ?
		""",
		(player_id, server_id, gem_name, number, number),
	)

	return gem_name


def get_player_gems(player_id: int, server_id: int) -> list[ItemEntry]:
	"""
	Get a player's gem collection.

	Returns:
		list[dict]: List of gems in the player's collection. Each gem is represented as a dictionary with 'gem_name'
			and 'quantity' keys.
	"""
	rows = query_all(
		"""
			SELECT gem_name, quantity FROM player_gems
			WHERE player_id = ? AND server_id = ?
			ORDER BY gem_name ASC
		""",
		(player_id, server_id),
	)

	entries = []
	for row in rows:
		name, qty = row

		entries.append(
			ItemEntry(
				name=name,
				quantity=qty,
				emote=Emotes.BLANK,
			)
		)

	return entries


def get_gem_progress(player_id: int, server_id: int, demon_id: int) -> int:
	"""Get gem meter progress."""
	result = query_one(
		"""
			SELECT gem_meter FROM player_demons
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	return result[0] if result else 0
