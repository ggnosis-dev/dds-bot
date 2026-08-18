from helpers.db import query_one, query_write


def update_server_in_db(server_id: int) -> bool:
	"""Update a server's data in the database."""
	rows_affected = query_write(
		"""
			INSERT INTO servers (server_id, player_count)
			VALUES (?, 1)
			ON CONFLICT (server_id) DO
				UPDATE SET player_count = player_count + 1
		""",
		(server_id,),
	)
	return rows_affected > 0


def check_server_exists(server_id: int) -> bool:
	"""
	Check if a server exists in the database.
	"""
	response = query_one(
		"""
			SELECT 1 FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)

	return response is not None


async def set_dedicated_channel(server_id: int, channel_id: int) -> bool:
	success = query_write(
		"""
			UPDATE servers SET dedicated_channel = ?
			WHERE server_id = ?
		""",
		(channel_id, server_id),
	)

	return True if success else False


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
	response = query_one(
		"""
			SELECT player_count FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)

	return response[0] if response else 0
