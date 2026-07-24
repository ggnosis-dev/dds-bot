from helpers.db import query_one, query_write


async def set_dedicated_channel(server_id: int, channel_id: int) -> bool:
	success = query_write(
		"""
			UPDATE servers SET dedicated_channel = ?
			WHERE server_id = ?
		""",
		(channel_id, server_id),
	)

	print(success)

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
