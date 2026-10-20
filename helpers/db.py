import sqlite3

from contextlib import contextmanager

from database_paths import PLAYERS_DB_PATH


@contextmanager
def transaction():
	"""This is essentially the same as __enter__, __exit__ context manager."""

	conn = _get_db_connection()

	try:
		# Avoids "database is locked" problem by making competing writers wait at BEGIN.
		conn.execute("BEGIN IMMEDIATE")
		# Pause here and take whatever is in the with block.
		yield conn
		conn.commit()
	except Exception as e:
		# Rollback everything if something goes wrong.
		conn.rollback()
		raise e
	finally:
		# Always gets run on success or failure.
		conn.close()


@contextmanager
def _connection(conn: sqlite3.Connection | None):
	"""Yield provided connection or start a fresh one, commits and closes it."""

	# Existing connection should run its queries.
	if conn is not None:
		yield conn
		return

	# When no connection provided, start a new one.
	new_conn = _get_db_connection()
	try:
		with new_conn:
			yield new_conn
	finally:
		new_conn.close()


def _get_db_connection() -> sqlite3.Connection:
	"""Helper method to get a connection to the players database."""

	conn = sqlite3.connect(PLAYERS_DB_PATH)
	conn.row_factory = sqlite3.Row

	# Enforce foreign key constraints for the connection.
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def query_one(query: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> sqlite3.Row:
	"""Queries and returns one entry."""
	try:
		with _connection(conn) as c:
			return c.execute(query, params).fetchone()
	except Exception as e:
		raise RuntimeError(f"ERROR: query_one failed: {e}\nQuery: {query}\nParams: {params}")


def query_all(query: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
	"""Queries and returns many entry."""
	try:
		with _connection(conn) as c:
			return c.execute(query, params).fetchall()
	except Exception as e:
		raise RuntimeError(f"ERROR: query_all failed: {e}\nQuery: {query}\nParams: {params}")


def query_write(query: str, params: tuple = (), conn: sqlite3.Connection | None = None) -> int:
	"""Queries and returns the rowcount which can be used for True/False checks."""
	try:
		with _connection(conn) as c:
			return c.execute(query, params).rowcount
	except Exception as e:
		raise RuntimeError(f"ERROR: query_write failed: {e}\nQuery: {query}\nParams: {params}")
