import sqlite3

from database_paths import PLAYERS_DB_PATH


def _get_db_connection() -> sqlite3.Connection:
	"""Helper method to get a connection to the players database."""
	conn = sqlite3.connect(PLAYERS_DB_PATH)
	conn.row_factory = sqlite3.Row

	# Enforce foreign key constraints for the connection.
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def query_one(query: str, params: tuple = ()) -> sqlite3.Row:
	"""Queries and returns one entry."""
	try:
		with _get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(query, params)
			response = cursor.fetchone()

			return response
	except Exception as e:
		print(f"ERROR: query_write failed: {e}\nQuery: {query}\nParams: {params}")
		raise RuntimeError(f"ERROR: query_one failed: {e}\nQuery: {query}\nParams: {params}")


def query_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
	"""Queries and returns many entry."""
	try:
		with _get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(query, params)

			return cursor.fetchall()
	except Exception as e:
		print(f"ERROR: query_write failed: {e}\nQuery: {query}\nParams: {params}")
		raise RuntimeError(f"ERROR: query_all failed: {e}\nQuery: {query}\nParams: {params}")


def query_write(query: str, params: tuple = ()) -> int:
	"""Queries and returns the rowcount which can be used for True/False checks."""
	try:
		with _get_db_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(query, params)

			return cursor.rowcount
	except Exception as e:
		print(f"ERROR: query_write failed: {e}\nQuery: {query}\nParams: {params}")
		raise RuntimeError(f"ERROR: query_write failed: {e}\nQuery: {query}\nParams: {params}")
