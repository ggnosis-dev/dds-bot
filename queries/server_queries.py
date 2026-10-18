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
