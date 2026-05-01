import sqlite3

from database_paths import PLAYERS_DB_PATH
from shared_enums import Personality


class DemonData:
	'''Data class for a demon's information.'''
	def __init__(self, id: int, name: str, race: str, rank: int, colour: int, personality_type: str, gem: str, image_url: str):
		'''
		Initialise the DemonData object with the provided attributes.
		
		Args:
			id (int): Demon's unique ID.
			name (str): Demon name.
			race (str): Demon race.
			rank (int): Demon's Rank signifies its strength and base rarity.
			colour (int): Colour is used for styling and various embeds.
			personality_type (str): Personality type, stored as a string in the database but converted to a Personality enum.
			image_url (str): Image URL for demon's art.
		'''
		self.id = id
		self.name = name
		self.race = race
		self.rank = rank
		self.colour = colour
		self.personality_type = Personality[personality_type]
		self.gem = gem
		self.image_url = image_url


class DemonQueries:
	'''Class for managing demon data retrieval from the database.'''
	def _convert_row_to_demon_data(self, row: tuple) -> DemonData:
		'''
		Convert retrieved DB row into a DemonData object.
		
		Args:
			row (tuple): A tuple containing demon data (id, name, race, rank, colour, personality, image_url).
		Returns:
			DemonData: Normalised DemonData object created from values provided.
		'''
		id, name, race, rank, colour, personality_type, gem, image_url = row
		return DemonData(
			id = id,
			name = name,
			race = race,
			rank = rank,
			colour = colour,
			personality_type = personality_type,
			gem = gem,
			image_url = image_url
		)


	def get_demon_by_id(self, demon_id: int) -> DemonData | None:
		'''
		Retrieve a demon's data from the database using its unique ID.
		
		Args:
			demon_id (int): Identifier of the demon to retrieve data for.
		Returns:
			DemonData | None: Demon's data if found, otherwise None.
		'''
		with sqlite3.connect(PLAYERS_DB_PATH) as conn:
			cursor = conn.cursor()
			row = cursor.execute('''
				SELECT id, name, race, rank, colour, personality, gem, image_url
				FROM demons 
				WHERE id = ?
			''', (demon_id,)).fetchone()

			if row:
				return self._convert_row_to_demon_data(row)
			return None


	def get_demon_id_by_name(self, demon_name: str) -> int | None:
		'''
		Retrieve a demon's ID from the database using its name.
		
		Args:
			demon_name (str): Name of the demon to retrieve the ID for.
		Returns:
			int | None: Demon's ID if found else None.
		'''
		with sqlite3.connect(PLAYERS_DB_PATH) as conn:
			cursor = conn.cursor()
			response = cursor.execute('''
				SELECT id FROM demons 
				WHERE LOWER(name) = LOWER(?)
			''', (demon_name,)).fetchone()

			return response[0] if response else None
	

	def get_demon_name_by_id(self, demon_id: int) -> str:
		'''
		Retrieve a demon's name from the database using its ID.

		Args:
			demon_id (int): Identifier of the demon to retrieve the name for.
		Returns:
			str: Demon's name if found, otherwise an empty string.
		'''
		with sqlite3.connect(PLAYERS_DB_PATH) as conn:
			cursor = conn.cursor()
			response = cursor.execute('''
				SELECT name FROM demons 
				WHERE id = ?
			''', (demon_id,)).fetchone()

			return response[0] if response else ""


	def get_random_demon(self) -> DemonData:
		'''
		Retrieve a random demon's data from the database.
		
		Returns:
			DemonData: Random demon's data.
		'''
		with sqlite3.connect(PLAYERS_DB_PATH) as conn:
			cursor = conn.cursor()
			row = cursor.execute('''
				SELECT id, name, race, rank, colour, personality, gem, image_url 
				FROM demons 
				ORDER BY RANDOM() 
				LIMIT 1
			''').fetchone()

			if not row:
				raise RuntimeError("ERROR: No demons found in the database.")

			return self._convert_row_to_demon_data(row)
	

	def get_demon_race_by_id(self, demon_id: int) -> str:
		'''
		Get demon's race from the database using its ID.

		Args:
			demon_id (int): Identifier of the demon to retrieve race for.
		Returns:
			str: Demon's race.
		'''
		with sqlite3.connect(PLAYERS_DB_PATH) as conn:
			cursor = conn.cursor()
			response = cursor.execute('''
				SELECT race FROM demons 
				WHERE id = ?
			''', (demon_id,)).fetchone()

			if response is None:
				raise RuntimeError(f"ERROR: Demon with ID {demon_id} not found in the database.")
			
			return response[0]