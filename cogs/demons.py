import sqlite3

from discord.ext import commands
from shared_enums import Personality


class DemonData:
	def __init__(self, id: int, name: str, race: str, rank: int, colour: int, personality_type: str, image_url: str):
		self.id = id
		self.name = name
		self.race = race
		self.rank = rank
		self.colour = colour
		self.personality_type = Personality[personality_type]
		self.image_url = image_url


class Demon(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot


	def get_demon_by_id(self, demon_id: int) -> DemonData | None:
		with sqlite3.connect('compendium.db') as conn:
			cursor = conn.cursor()
			row = cursor.execute('''
				SELECT id, name, race, rank, colour, personality, image_url 
				FROM demons 
				WHERE id = ?
			''', (demon_id,)).fetchone()

		if row:
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
		return None


	def get_demon_id_by_name(self, demon_name: str) -> int:
		with sqlite3.connect('compendium.db') as conn:
			cursor = conn.cursor()
			response = cursor.execute('''
				SELECT id FROM demons 
				WHERE LOWER(name) = LOWER(?)
			''', (demon_name,)).fetchone()

		return response[0] if response else -1


	def get_random_demon(self) -> DemonData | None:
		conn = sqlite3.connect('compendium.db')
		cursor = conn.cursor()
		cursor.execute('''
			SELECT id, name, race, rank, colour, personality, image_url 
			FROM demons 
			ORDER BY RANDOM() 
			LIMIT 1
		''')
		row = cursor.fetchone()
		conn.close()

		if row:
			id, name, race, rank, colour, personality_type, image_url = row
			demon = DemonData(
				id = id,
				name = name,
				race = race,
				rank = rank,
				colour = colour,
				personality_type = personality_type,
				image_url = image_url
			)
			return demon
		return None


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Demon(bot))
