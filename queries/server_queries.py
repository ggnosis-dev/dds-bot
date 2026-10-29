from time import time

from helpers.db import query_one, query_write


async def update_server_in_db(server_id: int) -> bool:
	"""Update a server's data in the database."""
	rows_affected = query_write(
		"""
			UPDATE servers
			SET player_count = player_count + 1
			WHERE server_id = ?
		""",
		(server_id,),
	)
	return rows_affected > 0


async def check_server_exists(server_id: int) -> bool:
	"""Check if a server exists in the database."""
	row = query_one(
		"""
			SELECT 1 FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)
	return row is not None


async def set_dedicated_channel(server_id: int, channel_id: int) -> bool:
	rows_affected = query_write(
		"""
			UPDATE servers
			SET dedicated_channel = ?
			WHERE server_id = ?
		""",
		(channel_id, server_id),
	)
	return rows_affected > 0


async def get_dedicated_channel(server_id: int) -> int | None:
	channel_id = query_one(
		"""
			SELECT dedicated_channel FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)

	return channel_id[0] if channel_id else None


async def get_player_count(server_id: int) -> int:
	row = query_one(
		"""
			SELECT player_count FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)

	return row[0] if row else 0


async def toggle_server_rankings(server_id: int, name: str | None, turn_on: bool) -> bool:
	rows_affected = query_write(
		"""
			UPDATE servers
			SET
				name_updated_last = CASE WHEN ? THEN ? ELSE name_updated_last END,
				show_in_ranking = ?,
				nickname = ?
			WHERE server_id = ?
		""",
		(turn_on, int(time()), turn_on, name, server_id),
	)
	return rows_affected > 0


async def get_last_updated_server_name(server_id: int) -> int:
	row = query_one(
		"SELECT name_updated_last FROM servers WHERE server_id = ?",
		(server_id,),
	)
	return row[0] if row and row[0] else 0
