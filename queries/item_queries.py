from sqlite3 import Connection

from entities.item_data import (
	INCENSE_RANK_INCREASE,
	GemCost,
	ItemEntry,
	ShopItemData,
	convert_row_to_item_entry,
	convert_rows_to_shop_item_data,
)
from helpers.db import query_all, query_one, query_write, transaction


async def get_player_inventory(player_id: int) -> list[ItemEntry]:
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
			WHERE pi.player_id = ?
		""",
		(player_id,),
	)

	entries = []
	for row in rows:
		entries.append(convert_row_to_item_entry(row))
	return entries


async def get_rags_item_list() -> list[ShopItemData]:
	"""Get all the available Rag's shop items."""

	rows = query_all(
		"""
			SELECT
				i.*,
				json_group_array(
					json_object(
						'gem_id', g.item_id,
						'name', g.name,
						'amount', si.amount
					)
				) AS cost
			FROM shop_items si
			JOIN items i ON i.item_id = si.item_id
			JOIN items g ON g.item_id = si.currency_gem_id
			GROUP BY i.item_id
			ORDER BY i.name
		""",
	)

	return convert_rows_to_shop_item_data(rows)


async def get_player_has_item(player_id: int, item_id: int) -> int:
	"""Check if a player has an item."""

	row = query_one(
		"""
			SELECT quantity FROM player_items
			WHERE player_id = ? AND item_id = ?
		""",
		(player_id, item_id),
	)
	return row[0] if row else 0


async def get_item_id_by_name(item_name: str) -> int | None:
	"""Get an item's ID by its name."""

	row = query_one(
		"""
			SELECT item_id FROM items
			WHERE LOWER(name) = LOWER(?)
		""",
		(item_name,),
	)

	return row[0] if row else None


async def give_player_item(player_id: int, item_id: int, conn: Connection | None = None) -> bool:
	"""Add item to inventory. If it doesn't exist already, set to 1."""

	rows_affected = query_write(
		"""
			INSERT INTO player_items (player_id, item_id, quantity)
			VALUES (?, ?, 1)
			ON CONFLICT (player_id, item_id) DO
			UPDATE SET quantity = quantity + 1
		""",
		(player_id, item_id),
		conn=conn,
	)
	return rows_affected > 0


async def use_incense(player_id: int, demon_id: int, item_id: int, number_to_use: int) -> bool:
	"""Use an incense item on a specified demon."""

	with transaction() as conn:
		# Remove one of the used item from the player's inventory.
		q1 = query_write(
			"""
				UPDATE player_items
				SET quantity = quantity - ?
				WHERE player_id = ?
					AND item_id = ?
					AND quantity >= ?
			""",
			(number_to_use, player_id, item_id, number_to_use),
			conn=conn,
		)

		if not q1:
			return False

		increase_by = number_to_use * INCENSE_RANK_INCREASE

		# Increase the demon's stored rank by increment.
		q2 = query_write(
			f"""
				UPDATE player_demons
				SET stored_rank = stored_rank + {increase_by}
				WHERE player_id = ? AND demon_id = ?
			""",
			(player_id, demon_id),
			conn=conn,
		)

		if not q2:
			conn.rollback()
			return False

		return True


async def can_demon_use_item(demon_id: int, item_id: int) -> bool:
	"""If the incense is exclusive to a specific race we should return False. Some incense are special and work for all."""

	row = query_one(
		"""
			SELECT 1 FROM items
			WHERE item_id = ?
				AND (
					exclusive_to IS NULL
					OR exclusive_to = (
						SELECT race_id FROM demons
						WHERE id = ?
					)
				)
		""",
		(item_id, demon_id),
	)

	return row is not None


async def attempt_purchase_item(player_id: int, item_id: int, cost: list[GemCost]) -> bool:
	"""
	Attempt to purchase item for the player. Checks if the player has enough gems and deducts the cost if they do.

	Args:
		item_id (int): ID of the item being purchased.
		cost (list[GemCost]): List of gems the item costs.
	Returns:
		bool: True if the purchase was successful, False if player didn't have enough.
	"""

	# Get the cost.
	with transaction() as conn:
		for c in cost:
			updated = query_write(
				"""
					UPDATE player_gems
					SET quantity = quantity - ?
					WHERE player_id = ?
						AND gem_id = ?
						AND quantity >= ?
				""",
				(c.amount, player_id, c.gem_id, c.amount),
				conn=conn,
			)

			# If there wasn't enough of any gem, rollback everything.
			if updated == 0:
				conn.rollback()
				return False

		await give_player_item(player_id, item_id, conn=conn)

	return True
