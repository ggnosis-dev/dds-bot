import sqlite3

from discord.ext import commands
from shared_enums import Personality


class DemonData:
	'''Data class for a demon's information.'''
	def __init__(self, id: int, name: str, race: str, rank: int, colour: int, personality_type: str, image_url: str):
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
		self.image_url = image_url


class Demon(commands.Cog):
	'''Cog for handling demon data retrieval and management.'''
	def __init__(self, bot: commands.Bot):
		'''Initialise the Demon cog with a reference to the bot instance.'''
		self.bot = bot


	def _convert_row_to_demon_data(self, row: tuple) -> DemonData:
		'''
		Convert retrieved DB row into a DemonData object.
		
		Args:
			row (tuple): A tuple containing demon data (id, name, race, rank, colour, personality, image_url).
		Returns:
			DemonData: Normalised DemonData object created from values provided.
		'''
		id, name, race, rank, colour, personality_type, image_url = row
		return DemonData(
			id = id,
			name = name,
			race = race,
			rank = rank,
			colour = colour,
			personality_type = personality_type,
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
		with sqlite3.connect('compendium.db') as conn:
			cursor = conn.cursor()
			row = cursor.execute('''
				SELECT id, name, race, rank, colour, personality, image_url 
				FROM demons 
				WHERE id = ?
			''', (demon_id,)).fetchone()

		if row:
			return self._convert_row_to_demon_data(row)
		return None


	def get_demon_id_by_name(self, demon_name: str) -> int:
		'''
		Retrieve a demon's ID from the database using its name.
		
		Args:
			demon_name (str): Name of the demon to retrieve the ID for.
		Returns:
			int: Demon's ID if found, otherwise -1.
		'''
		with sqlite3.connect('compendium.db') as conn:
			cursor = conn.cursor()
			response = cursor.execute('''
				SELECT id FROM demons 
				WHERE LOWER(name) = LOWER(?)
			''', (demon_name,)).fetchone()

		return response[0] if response else -1


	def get_random_demon(self) -> DemonData:
		'''
		Retrieve a random demon's data from the database.
		
		Returns:
			DemonData: Random demon's data.
		Raises:
			RuntimeError: If DB is empty.
		'''
		with sqlite3.connect('compendium.db') as conn:
			cursor = conn.cursor()
			row = cursor.execute('''
				SELECT id, name, race, rank, colour, personality, image_url 
				FROM demons 
				ORDER BY RANDOM() 
				LIMIT 1
			''').fetchone()

		if not row:
			raise RuntimeError("ERROR: No demons found in the database.")

		return self._convert_row_to_demon_data(row)


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	'''Add the Demon cog to the bot.'''
	await bot.add_cog(Demon(bot))
