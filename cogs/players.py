import json
import sqlite3

from discord.ext import commands

connection = sqlite3.connect('players.db')
cursor = connection.cursor()

# party and compendium are json
# https://www.sqlitetutorial.net/sqlite-json/
cursor.execute('''
	CREATE TABLE IF NOT EXISTS players (
		id INTEGER,
		server_id INTEGER,
		party TEXT,
		compendium TEXT,
		CONSTRAINT player_server_id PRIMARY KEY (id, server_id)
	)
''')

# Empty database for testing.
cursor.execute('DELETE FROM players')

connection.commit()
connection.close()


class PlayerData:
	def __init__(self, id: int, server_id: int, party: list[str], compendium: list[str]):
		self.id = id
		self.server_id = server_id
		self.party = party
		self.compendium = compendium


class Players(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	async def setup_player(self, ctx: commands.Context) -> bool:
		if ctx.guild is None:
			await ctx.send("ERROR: Could not determine server ID. How did you even get here?")
			return False

		id = ctx.author.id
		server_id = ctx.guild.id
		player_data = PlayerData(id, server_id, [], [])

		if self.check_player_exists(player_data):
			await ctx.send("You already have a profile set up on this server!")
			return False
		
		await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")

		self.save_player_to_db(player_data)
		
		await ctx.send("Your profile has been set up! You can now start playing.")
		return True


	def save_player_to_db(self, player: PlayerData):
		conn = sqlite3.connect('players.db')
		cursor = conn.cursor()
		cursor.execute('''
			INSERT INTO players (id, server_id, party, compendium) 
				 VALUES (?, ?, ?, ?)
		''', (player.id, player.server_id, json.dumps(player.party), json.dumps(player.compendium)))
		conn.commit()
		conn.close()

		print(f'INFO: Successfully saved player {player.id} on server {player.server_id} to database.')


	def check_player_exists(self, player: PlayerData) -> bool:
		conn = sqlite3.connect('players.db')
		cursor = conn.cursor()
		cursor.execute('''
			SELECT * FROM players 
				WHERE id = ? AND server_id = ?
		''', (player.id, player.server_id))
		result = cursor.fetchone()
		conn.close()

		return result != None
	

	async def add_demon_to_party(self, player_id: int, server_id: int, demon_id: int, demon_rank: int):
		conn = sqlite3.connect('players.db')
		cursor = conn.cursor()
		cursor.execute('''
			UPDATE players
				SET party = json_insert(party, '$[#]', json(?))
				WHERE id = ? AND server_id = ?
		''', (json.dumps({'id': demon_id, 'rank': demon_rank}), player_id, server_id))
		conn.commit()
		conn.close()

		print(f'INFO: Added demon with id {demon_id} and rank {demon_rank} to player {player_id} party on server {server_id}.')


	async def add_demon_to_compendium(self, player_id: int, server_id: int, demon_id: int, demon_rank: int) -> bool:
		conn = sqlite3.connect('players.db')
		cursor = conn.cursor()

		# Fetch the compendium.
		cursor.execute('''
			SELECT compendium FROM players 
				WHERE id = ? AND server_id = ?
		''', (player_id, server_id))
		row = cursor.fetchone()

		if row:
			comp = json.loads(row[0])

			# Check each entry.
			for entry in comp:
				# If demon is already in compendium, exit with False.
				if entry['id'] == demon_id:
					print(f'WARN: Demon with id {demon_id} already in player {player_id} compendium on server {server_id}.')
					conn.close()
					return False

		cursor.execute('''
			UPDATE players
				SET compendium = json_insert(compendium, '$[#]', json(?))
				WHERE id = ? AND server_id = ?
		''', (json.dumps({'id': demon_id, 'rank': demon_rank}), player_id, server_id))
		conn.commit()
		conn.close()

		print(f'INFO: Added demon with id {demon_id} and rank {demon_rank} to player {player_id} compendium on server {server_id}.')

		return True


async def setup(bot: commands.Bot):
	await bot.add_cog(Players(bot))
