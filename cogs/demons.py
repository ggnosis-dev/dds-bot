import sqlite3

from discord.ext import commands
from database_paths import PLAYERS_DB_PATH
from helpers import checks, players
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


class Demon(commands.Cog):
	'''Cog for demon-related commands and functionality.'''
	def __init__(self, bot):
		self.bot = bot
		self.demon_queries = DemonQueries()
		self.player_queries = players.Players()


	@checks.has_profile()
	@commands.command(name = 'select', aliases = ['s', 'sel'], description = "Select a demon to lead your party.")
	async def select_demon_command(self, ctx, *, demon_name: str) -> None:
		'''Select a demon to lead your party.'''
		demon_id = self.demon_queries.get_demon_id_by_name(demon_name)
		
		if demon_id == -1:
			await ctx.send(f"It seems a {demon_name} is not in your party.")
			return
		
		self.player_queries.set_selected_demon(ctx.author.id, ctx.guild.id, demon_id)
		await ctx.send(f"{demon_name} has been selected to lead your party!")



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


	def get_demon_id_by_name(self, demon_name: str) -> int:
		'''
		Retrieve a demon's ID from the database using its name.
		
		Args:
			demon_name (str): Name of the demon to retrieve the ID for.
		Returns:
			int: Demon's ID if found, otherwise -1.
		'''
		with sqlite3.connect(PLAYERS_DB_PATH) as conn:
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


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Demon(bot))
