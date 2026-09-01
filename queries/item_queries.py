import json

from entities.item_data import (
	INCENSE_RANK_INCREASE,
	ItemEntry,
	ShopItemData,
	convert_row_to_item_entry,
	convert_rows_to_shop_item_data,
)
from helpers.db import query_all, query_one, query_write
from queries import demon_queries


async def get_player_inventory(player_id: int, server_id: int) -> list[ItemEntry]:
	"""
	Get dictionary of name and quantity of items in player's inventory.

	Returns:
		dict[ItemEntry]: Item Name, Quantity pair.
	"""

	rows = query_all(
		"""
			SELECT i.name, i.emote, pi.quantity, i.description
			FROM player_items pi
			JOIN items i ON pi.item_id = i.item_id
			WHERE pi.player_id = ? AND pi.server_id = ?
		""",
		(player_id, server_id),
	)

	entries = []
	for row in rows:
		entries.append(convert_row_to_item_entry(row))
	return entries


async def get_rags_item_list() -> list[ShopItemData]:
	rows = query_all(
		"""
			SELECT * FROM items
			WHERE type = "sml_incense"
		""",
	)

	return convert_rows_to_shop_item_data(rows)


async def get_player_has_item(player_id: int, server_id: int, item_id: int) -> int:
	"""Check if a player has an item."""

	response = query_one(
		"""
			SELECT quantity FROM player_items
			WHERE player_id = ? AND server_id = ? AND item_id = ?
		""",
		(player_id, server_id, item_id),
	)

	return response[0] if response else 0


async def get_item_id_by_name(item_name: str) -> int | None:
	"""Get an item's ID by its name."""

	response = query_one(
		"""
			SELECT item_id FROM items
			WHERE LOWER(name) = LOWER(?)
		""",
		(item_name,),
	)

	return response[0] if response else None


async def give_player_item(player_id: int, server_id: int, item_id: int) -> bool:
	"""Add item to inventory. If it doesn't exist already, set to 1."""
	rows_affected = query_write(
		"""
			INSERT INTO player_items (player_id, server_id, item_id, quantity)
			VALUES (?, ?, ?, 1)
			ON CONFLICT (player_id, server_id, item_id) DO
			UPDATE SET quantity = quantity + 1
		""",
		(player_id, server_id, item_id),
	)

	return rows_affected > 0


async def use_incense(player_id: int, server_id: int, demon_id: int, item_id: int, number_to_use: int) -> bool:
	"""Use an incense item on a specified demon."""

	# Remove one of the used item from the player's inventory.
	q1 = query_write(
		"""
			UPDATE player_items
			SET quantity = quantity - ?
			WHERE player_id = ?
				AND server_id = ?
				AND item_id = ?
				AND quantity >= ?
		""",
		(number_to_use, player_id, server_id, item_id, number_to_use),
	)

	if not q1:
		return False

	increase_by = number_to_use * INCENSE_RANK_INCREASE

	# Increase the demon's stored rank by increment.
	q2 = query_write(
		f"""
			UPDATE player_demons
			SET stored_rank = stored_rank + {increase_by}
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	return bool(q2)


async def can_demon_use_item(demon_id: int, item_id: int) -> bool:
	"""If the incense is exclusive to a specific race we should return False. Some incense are special and work for all."""
	response = query_one(
		"SELECT UPPER(exclusive_to) FROM items WHERE item_id = ?",
		(item_id,),
	)

	exclusive_to = response[0] if response else None
	demon_race = await demon_queries.get_demon_race_by_id(demon_id)

	if exclusive_to is not None and demon_race != exclusive_to:
		return False
	return True


async def attempt_purchase_item(player_id: int, server_id: int, item_id: int, cost: dict) -> bool:
	"""
	Attempt to purchase item for the player. Checks if the player has enough gems and deducts the cost if they do.

	Args:
		item_id (str): ID of the item being purchased.
		cost (int): Cost of the item in gems.
	Returns:
		bool: True if the purchase was successful, False if player didn't have enough.
	"""

	response = query_one(
		"SELECT cost FROM items WHERE item_id = ?",
		(item_id,),
	)[0]

	cost = json.loads(response)
	gem_names = list(cost.keys())

	# Get number of placeholders for the IN clause.
	gem_placeholders = ",".join("?" * len(gem_names))

	# Get player's gem counts.
	rows = query_all(
		f"""
			SELECT gem_name, quantity FROM player_gems
			WHERE player_id = ? AND server_id = ? AND gem_name IN ({gem_placeholders})
		""",
		(player_id, server_id, *gem_names),
	)

	# Convert rows into a set for easier access. Gem: Quantity.
	player_gems = {row[0]: row[1] for row in rows}

	# Compare player's gems amount with cost.
	for gem, required_amount in cost.items():
		if player_gems.get(gem, 0) < required_amount:
			return False

	# Deduct gems.
	for gem, required_amount in cost.items():
		query_write(
			"""
				UPDATE player_gems
				SET quantity = quantity - ?
				WHERE player_id = ? AND server_id = ? AND gem_name = ?
			""",
			(required_amount, player_id, server_id, gem),
		)

	# Add item to inventory. If it doesn't exist already, set to 1.
	await give_player_item(player_id, server_id, item_id)

	return True
