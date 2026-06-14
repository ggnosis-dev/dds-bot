import json

from helpers.db import query_all, query_one, query_write
from queries import demon_queries

_ITEMS = {}

with open("data/items.json") as data:
	raw_items = json.load(data)

	# Build item lookups.
	for item_id, item_data in raw_items.items():
		_ITEMS[item_id] = item_data


def get_player_inventory(player_id: int, server_id: int) -> dict[str, int]:
	"""
	Get dictionary of name and quantity of items in player's inventory.

	Returns:
		dict[str, int]: Item Name, Quantity pair.
	"""
	response = query_all(
		"""
			SELECT item_id, quantity FROM player_items
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	inv = {}
	for item_id, quantity in response:
		item_data = _ITEMS.get(item_id)

		if item_data:
			inv[item_data["display_name"]] = quantity

	return inv


def get_player_has_item(player_id: int, server_id: int, item_id: str) -> bool:
	"""Check if a player has an item."""
	if item_id not in _ITEMS:
		raise ValueError(f"ERROR: Item with ID {item_id} not found in items data.")

	response = query_one(
		"""
		SELECT quantity FROM player_items
		WHERE player_id = ? AND server_id = ? AND item_id = ?
		""",
		(player_id, server_id, item_id),
	)[0]

	return response


def get_item_id_by_name(item_name: str) -> str | None:
	"""Get an item's ID by its name."""
	for item_id, item_data in _ITEMS.items():
		if item_data["display_name"].lower() == item_name.lower():
			return item_id
	return None


def use_incense(player_id: int, server_id: int, demon_id: int, item_id: str) -> bool:
	"""Use an incense item on a specified demon."""
	exclusive_to = _ITEMS[item_id].get("exclusive_to")
	demon_race = demon_queries.get_demon_race_by_id(demon_id)

	# Some incense may be special and work for all demons.
	if exclusive_to is not None:
		# If the incense is exclusive to a specific race we should return False.
		if demon_race != exclusive_to:
			return False

	# Increase the demon's stored rank by 3.
	q1 = query_write(
		"""
		UPDATE player_demons
		SET stored_rank = stored_rank + 3
		WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	# Remove one of the used item from the player's inventory.
	q2 = query_write(
		"""
		UPDATE player_items
		SET quantity = quantity - 1
		WHERE player_id = ? AND server_id = ? AND item_id = ?
		""",
		(player_id, server_id, item_id),
	)

	return bool(q1 and q2)
