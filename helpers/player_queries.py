import sqlite3

from database_paths import PLAYERS_DB_PATH
from discord.ext import commands
from shared_enums import DemonRegistration


GEM_EXP_MULTIPLIER = 1
GEM_METER_FULL = 100


class PlayerData:
	def __init__(self, player_id: int, server_id: int, selected_demon_id: int, mag: int, daily_timer: int):
		self.player_id = player_id
		self.server_id = server_id
		self.selected_demon_id = selected_demon_id
		self.mag = mag
		self.daily_timer = daily_timer


class ServerCompendiumDemon:
	def __init__(self, player_id: int, server_id: int, demon_id: int, stored_rank: int):
		self.player_id = player_id
		self.server_id = server_id
		self.demon_id = demon_id
		self.stored_rank = stored_rank


class PlayerQueries:
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

		player_id = ctx.author.id
		server_id = ctx.guild.id

		if self.check_player_exists(player_id, server_id):
			await ctx.send("You already have a profile set up on this server!")
			return False
		
		await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")
		self.save_player_to_db(player_id, server_id)
		self.update_server_in_db(server_id)
		await ctx.send("Your profile has been set up!")

		return True


	def save_player_to_db(self, player_id: int, server_id: int) -> bool:
		'''
		Save a new player's data to the database.

		Args:
			player_id (int): Player ID that needs saving.
			server_id (int): Server ID player belongs to.
		Returns:
			bool: True on successful, False on fail.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				INSERT INTO players (player_id, server_id) 
					VALUES (?, ?)
			''', (player_id, server_id))
			print(f'INFO: New player added: {player_id} | Server {server_id}.')
			return cursor.rowcount > 0


	def update_server_in_db(self, server_id: int) -> bool:
		'''
		Update a server's data in the database.

		Args:
			server_id (int): Server ID to save.
		Returns:
			bool: True on successful, False on fail.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				INSERT INTO servers (server_id, player_count) 
				VALUES (?, 1)
				ON CONFLICT (server_id) DO UPDATE SET
					player_count = player_count + 1
			''', (server_id,))
			return cursor.rowcount > 0


	def check_player_exists(self, player_id, server_id) -> bool:
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
			''', (player_id, server_id)).fetchone()
			return result is not None
		
	
	async def get_player(self, player_id, server_id) -> PlayerData | None:
		'''
		Get the properties of the player.

		Args:
			player_id (int): Player ID.
			server_id (int): Sever ID player belongs to.
		Returns:
			PlayerData: A data class of player properties.
		'''
		with self.get_db_connection() as conn:
			conn.row_factory = sqlite3.Row
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT * FROM players 
				WHERE player_id = ? AND server_id = ?
			''', (player_id, server_id)).fetchone()
			
			if result is None: return None

			return PlayerData(
				player_id = result['player_id'],
				server_id = result['server_id'],
				selected_demon_id = result['selected_demon_id'],
				mag = result['mag'],
				daily_timer = result['daily_timer']
			)
		
	async def set_daily_timer(self, player_id: int, server_id: int, time: int) -> bool:
		'''
		Set the player's daily timer.
		
		Args:
			player_id (int): Player ID.
			server_id (int): Sever ID player belongs to.
			time (int): Time to set the daily timer to.
		Returns:
			bool: True if successful, False otherwise.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('''
				UPDATE players
				SET daily_timer = ?
				WHERE player_id = ? AND server_id = ?
			''', (time, player_id, server_id))

			return cursor.rowcount > 0


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
			if exists_in_comp: return False
			
			cursor.execute('''
				INSERT INTO player_demons (player_id, server_id, demon_id, stored_rank, in_party)
				VALUES (?, ?, ?, ?, 0)
			''', (player_id, server_id, demon_id, demon_rank))

			return True
		
	
	async def add_demon_to_server_compendium(
		self, 
		player_id: int, 
		server_id: int, 
		demon_id: int, 
	) -> bool:
		'''
		Add a demon to the server's compendium and mark it on loan.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			demon_id (int): Demon's ID.
		Returns:
			bool: True if the demon was added, False if it already exists.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			exists_in_comp = cursor.execute('''
				SELECT 1 FROM server_demons
				WHERE server_id = ? AND demon_id = ?
			''', (server_id, demon_id)).fetchone()

			# Return early if demon is already in compendium to avoid dupes.
			if exists_in_comp: return False

			# Insert reference to player's demon into the compendium.
			cursor.execute('''
				INSERT INTO server_demons (player_id, server_id, demon_id)
				VALUES (?, ?, ?)
			''', (player_id, server_id, demon_id))

			# Update player's demon with the on loan flag.
			cursor.execute('''
				UPDATE player_demons SET on_loan = 1
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (player_id, server_id, demon_id))

			return True
		
	
	async def get_server_compendium_demon(self, server_id: int, demon_id: int) -> ServerCompendiumDemon:
		with self.get_db_connection() as conn:
			conn.row_factory = sqlite3.Row
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT sd.*, pd.stored_rank FROM server_demons sd
				JOIN player_demons pd
					ON sd.player_id = pd.player_id
				  		AND sd.server_id = pd.server_id
				  		AND sd.demon_id = pd.demon_id
				WHERE sd.server_id = ? AND sd.demon_id = ? 
			''', (server_id, demon_id)).fetchone()

			return ServerCompendiumDemon(
				player_id = result['player_id'],
				server_id = result['server_id'],
				demon_id = result['demon_id'],
				stored_rank = result['stored_rank']
			)


	async def replace_server_compendium_demon(self, player_id, server_id, demon_id) -> None:
		# await self.return_server_comp_demon(server_id, demon_id)

		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Release old loaned demon.
			cursor.execute('''
				UPDATE player_demons SET on_loan = 0
				WHERE server_id = ? AND demon_id = ?
					AND player_id = (
				  		SELECT player_id FROM server_demons
				  		WHERE server_id = ? AND demon_id = ?
				  )
			''', (server_id, demon_id, server_id, demon_id))

			# Update compendium entry.
			cursor.execute('''
				UPDATE server_demons SET player_id = ?
				WHERE server_id = ? AND demon_id = ?
			''', (player_id, server_id, demon_id))

			# Set on loan on demon.
			cursor.execute('''
				UPDATE player_demons SET on_loan = 1
				WHERE player_id = ? AND server_id = ? AND demon_id = ?
			''', (player_id, server_id, demon_id))


	async def return_server_comp_demon(self, server_id, demon_id) -> bool:
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Set on loan back to 0.
			cursor.execute('''
				UPDATE player_demons SET on_loan = 0
				WHERE server_id = ? AND demon_id = ?
					AND player_id = (
				  		SELECT player_id FROM server_demons
				  		WHERE server_id = ? AND demon_id = ?
				  )
			''', (server_id, demon_id, server_id, demon_id))

			# Delete the compendium entry.
			cursor.execute('''
				DELETE FROM server_demons
				WHERE server_id = ? AND demon_id = ?
			''', (server_id, demon_id))

			return cursor.rowcount > 0


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
				SELECT d.id, d.name, d.race, d.personality, pd.stored_rank, pd.in_party, d.gem
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


	async def increase_gems(self, player_id: int, server_id: int, demon_id: int) -> bool:
		'''
		Add to player's gem meter and add a gem to their count if over a threshold.
		Return whether a gem has been found.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
			selected_demon_id (int): Player's selected demon ID to determine which gem meter to increase.
			exp (int): Amount to increase the gem meter by.
		Returns:
			bool: True if gem was found, False otherwise.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()

			# Get gem type and the player's stored rank for demon.
			gem_name, stored_rank = cursor.execute('''
				SELECT d.gem, pd.stored_rank FROM demons d
				JOIN player_demons pd ON pd.demon_id = d.id
				WHERE d.id = ?
			''', (demon_id,)).fetchone()

			if gem_name is None: return False

			stored_rank = stored_rank * GEM_EXP_MULTIPLIER

			# Increase gem meter by exp, returning meter value.
			cursor.execute('''
				INSERT INTO player_gems (player_id, server_id, gem_name, meter, quantity)
				VALUES (?, ?, ?, ?, 0)
				ON CONFLICT (player_id, server_id, gem_name) DO
				UPDATE SET meter = meter + excluded.meter
				RETURNING meter
			''', (player_id, server_id, gem_name, stored_rank))

			# Get the meter value after the update to check if a gem has been found.
			meter_val = cursor.fetchone()[0]
			print(f"DEBUG: Player {player_id} | Server {server_id} | Gem {gem_name} meter: {meter_val:.2f}")

			# Add gem to count and reset meter if gem found.
			if meter_val >= GEM_METER_FULL:
				cursor.execute('''
					UPDATE player_gems
					SET meter = 0, quantity = quantity + 1
					WHERE player_id = ? AND server_id = ? AND gem_name = ?
				''', (player_id, server_id, gem_name))

				return True
			return False
		

	def get_player_gems(self, player_id: int, server_id: int) -> list[tuple]:
		'''
		Get a player's gem collection.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID the player belongs to.
		Returns:
			list[dict]: List of gems in the player's collection. Each gem is represented as a dictionary with 'gem_name' and 'quantity' keys.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT gem_name, quantity FROM player_gems
				WHERE player_id = ? AND server_id = ?
				ORDER BY gem_name ASC
			''', (player_id, server_id)).fetchall()

			return result if result else []
		
	
	def get_gem_progress(self, player_id: int, server_id: int, gem_name: str) -> int:
		'''Get gem meter progress.'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			result = cursor.execute('''
				SELECT meter FROM player_gems
				WHERE player_id = ? AND server_id = ? AND gem_name = ?
			''', (player_id, server_id, gem_name)).fetchone()

			return result[0] if result else 0
		
		
	def attempt_purchase_item(self, player_id: int, server_id: int, item_id: str, cost: dict) -> bool:
		'''
		Attempt to purchase an item for the player. Checks if the player has enough gems and deducts the cost if they do.

		Args:
			player_id (int): Player ID.
			server_id (int): Server ID.
			item_id (str): ID of the item being purchased.
			cost (int): Cost of the item in gems.
		Returns:
			bool: True if the purchase was successful, False if player didn't have enough.
		'''
		with self.get_db_connection() as conn:
			cursor = conn.cursor()
			gem_names = list(cost.keys())

			# Get number of placeholders for the IN clause.
			gem_placeholders = ','.join('?' * len(gem_names))
			
			# Get player's gem counts.
			rows = cursor.execute(f'''
				SELECT gem_name, quantity FROM player_gems
				WHERE player_id = ? AND server_id = ? AND gem_name IN ({gem_placeholders})
			''', (player_id, server_id, *gem_names)).fetchall()

			# Convert rows into a set for easier access. Gem: Quantity.
			player_gems = {row[0]: row[1] for row in rows}

			# Compare player's gems with cost.
			for gem, required_amount in cost.items():
				if player_gems.get(gem, 0) < required_amount:
					return False
			
			# Deduct gems.
			for gem, required_amount in cost.items():
				cursor.execute('''
					UPDATE player_gems
					SET quantity = quantity - ?
					WHERE player_id = ? AND server_id = ? AND gem_name = ?
				''', (required_amount, player_id, server_id, gem))

			# Add item to inventory. If it doesn't exist already, set to 1.
			cursor.execute('''
				INSERT INTO player_items (player_id, server_id, item_id, quantity)
				VALUES (?, ?, ?, 1)
				ON CONFLICT (player_id, server_id, item_id) DO
				UPDATE SET quantity = quantity + 1
			''', (player_id, server_id, item_id))

			return True