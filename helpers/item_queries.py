import json
import sqlite3

from helpers.demon_queries import DemonQueries
from database_paths import PLAYERS_DB_PATH


class ItemQueries:
	'''
		Use an item from the player's inventory.
		
		Args:
			player_id (int): ID of the player using the item.
			server_id (int): ID of the server where the item is being used.
			item_id (str): ID of the item to use.
	'''
	def __init__(self):
		with open('data/items.json', 'r') as data:
			raw_items = json.load(data)

		self.items = {}

		# Build item lookups.
		for item, item_data in raw_items.items():
			self.items[item] = item_data


	def _get_db_connection(self) -> sqlite3.Connection:
		'''Helper method to get a connection to the players database.'''
		conn = sqlite3.connect(PLAYERS_DB_PATH)

		# Enforce foreign key constraints for the connection.
		conn.execute('PRAGMA foreign_keys = ON')
		return conn
	

	def get_player_items(self, player_id: int, server_id: int) -> dict[str, int]:
		'''Get dictionary of name and quantity of items in player's inventory.'''
		with self._get_db_connection() as conn:
			cursor = conn.cursor()

			cursor.execute('''
				SELECT item_id, quantity FROM player_items 
				WHERE player_id = ? AND server_id = ?
			''', (player_id, server_id))

			results = cursor.fetchall()

			items = {}
			for item_id, quantity in results:
				item_data = self.items.get(item_id)
				if item_data:
					items[item_data['display_name']] = quantity

			return items


	def get_player_has_item(self, player_id: int, server_id: int, item_id: str) -> bool:
		if item_id not in self.items:
			raise ValueError(f"ERROR: Item with ID {item_id} not found in items data.")
		
		with self._get_db_connection() as conn:
			cursor = conn.cursor()

			cursor.execute('''
				SELECT quantity FROM player_items 
				WHERE player_id = ? AND server_id = ? AND item_id = ?
			''', (player_id, server_id, item_id))

			result = cursor.fetchone()

			if result is None or result[0] == 0:
				return False
			return True
		

	def get_item_id_by_name(self, item_name: str) -> str | None:
		for item_id, item_data in self.items.items():
			if item_data['display_name'].lower() == item_name.lower():
				return item_id
		return None


	def use_incense(self, player_id: int, server_id: int, demon_id: int, item_id: str) -> bool:
		exclusive_to = self.items[item_id].get('exclusive_to')
		demon_race = DemonQueries().get_demon_race_by_id(demon_id)

		# Some incense may be special and work for all demons.
		if exclusive_to is not None:
			# If the incense is exclusive to a specific race we should return False.
			if demon_race != exclusive_to:
				return False

		with self._get_db_connection() as conn:
			cursor = conn.cursor()

			# Increase the demon's stored rank by 3.
			cursor.execute('''
				UPDATE player_demons
				SET stored_rank = stored_rank + 3
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (player_id, server_id, demon_id))

			# Remove one of the used item from the player's inventory.
			cursor.execute('''
				UPDATE player_items
				SET quantity = quantity - 1
				WHERE player_id = ? AND server_id = ? AND item_id = ?
			''', (player_id, server_id, item_id))

			return True
