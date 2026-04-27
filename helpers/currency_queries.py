import sqlite3

from database_paths import PLAYERS_DB_PATH


def _get_db_connection() -> sqlite3.Connection:
	'''Helper method to get a connection to the players database.'''
	conn = sqlite3.connect(PLAYERS_DB_PATH)

	# Enforce foreign key constraints for the connection.
	conn.execute('PRAGMA foreign_keys = ON')
	return conn


def get_mag(player_id: int, server_id: int) -> int:
	'''Get the amount of magnetite a player has.'''
	with _get_db_connection() as conn:
		cursor = conn.cursor()

		cursor.execute('''
			SELECT mag FROM players
			WHERE player_id = ? AND server_id = ?
		''', (player_id, server_id))

		result = cursor.fetchone()
		return result[0] if result else 0


def update_mag(player_id: int, server_id: int, amount: int) -> bool:
	'''
	Update the amount of magnetite a player has.
	
	Args:
		player_id (int): ID of the player.
		server_id (int): ID of the server.
		amount (int): Amount of magnetite to add (positive) or subtract (negative).
	Returns:
		bool: True if the update was successful, False otherwise.
	'''
	with _get_db_connection() as conn:
		cursor = conn.cursor()

		cursor.execute('''
			UPDATE players
			SET mag = mag + ?
			WHERE player_id = ? AND server_id = ?
		''', (amount, player_id, server_id))

		return cursor.rowcount > 0