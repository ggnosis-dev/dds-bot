import sqlite3

from database_paths import PLAYERS_DB_PATH


def get_db_connection() -> sqlite3.Connection:
	"""Helper method to get a connection to the players database."""
	conn = sqlite3.connect(PLAYERS_DB_PATH)

	# Enforce foreign key constraints for the connection.
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def query_one(query: str, params: tuple = ()) -> tuple | None:
	"""Queries and returns one entry."""
	with get_db_connection() as conn:
		cursor = conn.cursor()
		cursor.execute(query, params)

		return cursor.fetchone()


def query_many(query: str, params: tuple = ()) -> list[tuple]:
	"""Queries and returns many entry."""
	with get_db_connection() as conn:
		cursor = conn.cursor()
		cursor.execute(query, params)

		return cursor.fetchall()


def query_count(query: str, params: tuple = ()) -> int:
	"""Queries and returns the rowcount."""
	with get_db_connection() as conn:
		cursor = conn.cursor()
		cursor.execute(query, params)

		return cursor.rowcount
