import sqlite3

from discord.ext import commands
from shared_enums import DemonRegistration


# https://www.sqlitetutorial.net/sqlite-json/
with sqlite3.connect('players.db') as conn:
	cursor = conn.cursor()
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS players (
			player_id 		INTEGER,
			server_id 		INTEGER,
			CONSTRAINT player_server_id PRIMARY KEY (player_id, server_id)
		)
	''')

	cursor.execute('''		   
		CREATE TABLE IF NOT EXISTS player_demons (
			player_id 		INTEGER,
			server_id 		INTEGER,
			demon_id		INTEGER,
			stored_rank		INTEGER,
			in_party		INTEGER CHECK (in_party IN (0, 1)),
			UNIQUE(player_id, server_id, demon_id)
		)
	''')

	# Index for faster lookup of player's parties and compendiums.
	cursor.execute('''
		CREATE INDEX IF NOT EXISTS idx_player_demons ON player_demons(player_id, server_id)
	''')

	# TESTS:
	# cursor.execute('DELETE FROM players')
	# cursor.execute('DELETE FROM player_demons')
	# cursor.execute('UPDATE player_demons SET in_party = 0')


class PlayerData:
	def __init__(self, id: int, server_id: int):
		self.id = id
		self.server_id = server_id


class Players(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	async def setup_player(self, ctx: commands.Context) -> bool:
		if ctx.guild is None:
			await ctx.send("ERROR: Could not determine server ID. How did you even get here?")
			return False

		id = ctx.author.id
		server_id = ctx.guild.id
		player_data = PlayerData(id, server_id)

		# Exit with False if player exists.
		if self.check_player_exists(player_data):
			await ctx.send("You already have a profile set up on this server!")
			return False
		
		await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")

		self.save_player_to_db(player_data)
		
		await ctx.send("Your profile has been set up!")
		return True


	def save_player_to_db(self, player: PlayerData):
		with sqlite3.connect('players.db') as conn:
			cursor = conn.cursor()
			cursor.execute('''
				INSERT INTO players (player_id, server_id) 
					VALUES (?, ?)
			''', (player.id, player.server_id))
			print(f'INFO: New player added: {player.id} | Server {player.server_id}.')


	def check_player_exists(self, player: PlayerData) -> bool:
		with sqlite3.connect('players.db') as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT * FROM players 
					WHERE player_id = ? AND server_id = ?
			''', (player.id, player.server_id)).fetchone()
			return result is not None
	

	async def set_demon_in_party(self, player_id: int, server_id: int, demon_id: int, party_add: bool = True) -> bool:
		with sqlite3.connect('players.db') as conn:
			cursor = conn.cursor()
			cursor.execute('''
				UPDATE player_demons 
				SET in_party = ? 
				WHERE player_id = ? AND server_id = ? AND demon_id = ? AND in_party != ?
			''', (party_add, player_id, server_id, demon_id, party_add))

			# Returns True if a row was updated, False otherwise.
			return cursor.rowcount > 0


	async def add_demon_to_compendium(self, player_id: int, server_id: int, demon_id: int, demon_rank: int) -> bool:
		with sqlite3.connect('players.db') as conn:
			cursor = conn.cursor()

			# Check if demon is already in compendium.
			exists_in_comp = cursor.execute('''
				SELECT 1 FROM player_demons
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (player_id, server_id, demon_id)).fetchone()

			# Return early if demon is already in compendium to avoid dupes.
			if exists_in_comp : return False
			
			cursor.execute('''
				INSERT INTO player_demons (player_id, server_id, demon_id, stored_rank)
				VALUES (?, ?, ?, ?)
			''', (player_id, server_id, demon_id, demon_rank))

			return True
		
	async def check_demon_registration(self, user_id: int, guild_id: int, demon_id: int) -> DemonRegistration:
		'''
		Check if a demon is in the player's party or compendium. Function will return True if in the party,
		False if it's in the compendium but not the party, and None if it doesn't have an entry at all.
		'''
		with sqlite3.connect('players.db') as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT in_party FROM player_demons 
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (user_id, guild_id, demon_id)).fetchone()

		match result:
			case (1,) 	: return DemonRegistration.IN_PARTY
			case (0,)	: return DemonRegistration.IN_COMP
			case _		: return DemonRegistration.UNREGISTERED


async def setup(bot: commands.Bot):
	await bot.add_cog(Players(bot))
