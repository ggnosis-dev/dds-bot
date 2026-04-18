import sqlite3

from database_paths import PLAYERS_DB_PATH
from discord.ext import commands
from shared_enums import DemonRegistration


class PlayerData:
	'''Data class for a player's information.'''
	def __init__(self, id: int, server_id: int) -> None:
		'''
		Initialize a new PlayerData instance.
		TODO: Add currencies.

		Args:
			id (int): The player's ID.
			server_id (int): The server ID the player belongs to.
		'''
		self.id = id
		self.server_id = server_id


class Players:
	def get_db_connection(self) -> sqlite3.Connection:
		'''Helper method to get a connection to the players database.'''
		conn = sqlite3.connect(PLAYERS_DB_PATH)

		# Enforce foreign key constraints for the connection.
		conn.execute('PRAGMA foreign_keys = ON')
		return conn

	'''Class for querying player data and updates to the database.'''
	async def setup_player(self, ctx: commands.Context) -> bool:
		'''
		Set up a new player in the database if they don't already have a profile.

		Returns:
			bool: True if a new profile was created, False if player already exists.
		'''
		if ctx.guild is None:
			raise RuntimeError("ERROR: Server ID could not be determined.")

		id = ctx.author.id
		server_id = ctx.guild.id

		if self.check_player_exists(id, server_id):
			await ctx.send("You already have a profile set up on this server!")
			return False
		
		await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")
		player_data = PlayerData(id, server_id)
		self.save_player_to_db(player_data)
		await ctx.send("Your profile has been set up!")

		return True


	def save_player_to_db(self, player: PlayerData) -> None:
		'''
		Save a new player's data to the database.

		Args:
			player (PlayerData): Player's data that needs saving.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				INSERT INTO players (player_id, server_id) 
					VALUES (?, ?)
			''', (player.id, player.server_id))
			print(f'INFO: New player added: {player.id} | Server {player.server_id}.')


	def check_player_exists(self, player_id, player_server) -> bool:
		'''
		Check if a player already exists in the database.

		Args:
			player_id (int): Player ID.
			player_server (int): Server ID the player belongs to.
		Returns:
			bool: True if the player exists, False otherwise.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT * FROM players 
					WHERE player_id = ? AND server_id = ?
			''', (player_id, player_server)).fetchone()
			return result is not None
	

	async def set_demon_in_party(
		self, 
		player_id: int, 
		server_id: int, 
		demon_id: int, 
		party_add: bool = True
	) -> bool:
		'''
		Manage whether to add or remove a demon from a player's party.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			demon_id (int): Demon's ID.
			party_add (bool): True to add to party, False to remove from party.
		Returns:
			bool: True if the demon's status was updated, False otherwise.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				UPDATE player_demons 
				SET in_party = ? 
				WHERE player_id = ? AND server_id = ? AND demon_id = ? AND in_party != ?
			''', (party_add, player_id, server_id, demon_id, party_add))

			return cursor.rowcount > 0


	async def add_demon_to_compendium(
		self, 
		player_id: int, 
		server_id: int, 
		demon_id: int, 
		demon_rank: int
	) -> bool:
		'''
		Add a demon to the player's compendium if it doesn't already exist.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			demon_id (int): Demon's ID.
			demon_rank (int): Demon's rank.
		Returns:
			bool: True if the demon was added, False if it already exists.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Check if demon is already in compendium.
			exists_in_comp = cursor.execute('''
				SELECT 1 FROM player_demons
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (player_id, server_id, demon_id)).fetchone()

			# Return early if demon is already in compendium to avoid dupes.
			if exists_in_comp : return False
			
			cursor.execute('''
				INSERT INTO player_demons (player_id, server_id, demon_id, stored_rank, in_party)
				VALUES (?, ?, ?, ?, 0)
			''', (player_id, server_id, demon_id, demon_rank))

			return True
		

	async def check_demon_registration(
		self, 
		user_id: int, 
		server_id: int, 
		demon_id: int
	) -> DemonRegistration:
		'''
		Check a demon's current state of registration for a specific player. 

		Args:
			user_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			demon_id (int): Demon's ID.
		Returns:
			DemonRegistration: Enum indicating the demon's registration status.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT in_party FROM player_demons 
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (user_id, server_id, demon_id)).fetchone()

		match result:
			case (1,) 	: return DemonRegistration.IN_PARTY
			case (0,)	: return DemonRegistration.IN_COMP
			case _		: return DemonRegistration.UNREGISTERED


	async def check_party(self, user_id: int, server_id: int) -> list[dict]:
		'''
		Query the database for the player's current party. Joins the player_demons table with the demon database.

		Returns:
			list[dict]: List of demons in the player's party. Includes ID, name, race and stored_rank.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Retrieve the player's party.
			result = cursor.execute('''
				SELECT d.id, d.name, d.race, pd.stored_rank
				FROM player_demons pd
				JOIN demons d ON pd.demon_id = d.id
				WHERE pd.player_id = ? AND pd.server_id = ? AND pd.in_party = 1
				ORDER BY d.race ASC, d.id ASC
			''', (user_id, server_id)).fetchall()
			
			return result if result else []
	

	async def check_compendium(self, user_id: int, server_id: int) -> list[dict]:
		'''
		Query the database for the player's encountered demons. Joins the player_demons table with the demon database.

		Returns:
			list[dict]: List of demons in the player's compendium. Includes ID, name, race, personality, stored_rank, and in_party status.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Use LEFT JOIN to get all demons. stored_rank will be NULL if player hasn't encountered them.
			result = cursor.execute('''
				SELECT d.id, d.name, d.race, d.personality, pd.stored_rank, pd.in_party
				FROM demons d
				LEFT JOIN player_demons pd ON pd.demon_id = d.id
					AND pd.player_id = ? AND pd.server_id = ?
				ORDER BY d.race ASC, d.id ASC
			''', (user_id, server_id)).fetchall()

			return result if result else []


	def set_selected_demon(self, player_id: int, server_id: int, demon_id: int) -> None:
		'''
		Set the selected demon for the player. The player's selected demon will hunt for their gem type,
		and have other uses in the future.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			demon_id (int): Demon's ID to set as selected.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				UPDATE players
				SET selected_demon_id = ?
				WHERE player_id = ? AND server_id = ?
			''', (demon_id, player_id, server_id))


	def get_selected_demon_id(self, player_id: int, server_id: int) -> int | None:
		'''
		Get the player's selected demon ID.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
		Returns:
			int | None: The selected demon's ID if it exists, otherwise None.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT selected_demon_id FROM players
				WHERE player_id = ? AND server_id = ?
			''', (player_id, server_id)).fetchone()

			return result[0] if result else None


	def add_gem_info(self, player_id: int, server_id: int, gem_name: str) -> None:
		'''
		Add an entry for the selected demon's gem information if it doesn't already exist.
		TODO: Should be used when selecting a demon.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			gem_name (str): Name of the gem associated with selected demon.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			cursor.execute('''
				  INSERT OR IGNORE INTO player_gems (player_id, server_id, gem_name, meter)
				  VALUES (?, ?, ?, 0)
			''', (player_id, server_id, gem_name))


	async def increase_gems(self, player_id: int, server_id: int, gem_name: str, exp: int) -> bool:
		'''
		Add to player's gem meter and add a gem to their count if over a threshold.
		Return whether a gem has been found.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			gem_name (str): Name of the gem associated with the selected demon.
			exp (int): Amount to increase the gem meter by.
		Returns:
			bool: True if gem was found, False otherwise.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Increase gem meter by exp, returning meter value.
			cursor.execute('''
				UPDATE player_gems
				SET meter = meter + ?
				WHERE player_id = ? AND server_id = ? AND gem_name = ?
				RETURNING meter
			''', (exp, player_id, server_id, gem_name))

			# Get the meter value after the update to check if a gem has been found.
			meter_val = cursor.fetchone()[0]

			# Add gem to count and reset meter if gem found.
			if meter_val >= 100:
				cursor.execute('''
					UPDATE player_gems
					SET meter = 0, quantity = quantity + 1
					WHERE player_id = ? AND server_id = ? AND gem_name = ?
				''', (player_id, server_id, gem_name))

				return True
			return False


		# with self.get_db_connection() as conn:
		# 	cursor = conn.cursor()

		# 	# Check if demon is already in compendium.
		# 	exists_in_comp = cursor.execute('''
		# 		SELECT 1 FROM player_demons
		# 		WHERE player_id = ? AND server_id = ? AND demon_id = ?
		# 	''', (player_id, server_id, demon_id)).fetchone()

		# 	# Return early if demon is already in compendium to avoid dupes.
		# 	if exists_in_comp : return False
			
		# 	cursor.execute('''
		# 		INSERT INTO player_demons (player_id, server_id, demon_id, stored_rank, in_party)
		# 		VALUES (?, ?, ?, ?, 0)
		# 	''', (player_id, server_id, demon_id, demon_rank))

		# 	return True