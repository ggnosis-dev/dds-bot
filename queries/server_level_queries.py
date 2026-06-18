from entities.server_data import ServerStats
from helpers.db import query_one, query_write

"""
Server level:
	- Every time a demon is added to the Server COMP, add their rank to the XP.
	- If XP reaches a moving threshold, server levels up.
	- Have a list of perks to provide, right now we'll limit them just to rank cap increases.
"""

XP_START = 10
XP_END = 100
MAX_LEVEL = 10


# https://gist.github.com/laundmo/b224b1f4c8ef6ca5fe47e132c8deab56
def get_xp_threshold(level: int) -> int:
	"""XP required to hit next level using a linear interpolate. Eases in due to the power of 2."""
	# level / (MAX_LEVEL - 1) ** 2
	# 9 / (9)^2 = 0.1111
	# 8 / (9)^2 = 0.0987
	# (level / (MAX_LEVEL - 1)) ** 2
	# (9 / (10 - 1))^2 = 1
	# (8 / (9))^2 = 0.79
	point_t = (level / (MAX_LEVEL - 1)) ** 2
	return int((1 - point_t) * XP_START + point_t * XP_END)


async def try_server_level_up(server_id: int, rank: int) -> bool:
	# Update server level XP and return the XP.
	xp, server_level = query_one(
		"""
			UPDATE servers
			SET server_level_xp = server_level_xp + ?
			WHERE server_id = ?
			RETURNING server_level_xp, server_level
		""",
		(rank, server_id),
	)

	# Check to see if we are higher or lower than the threshold to next level.
	while server_level < MAX_LEVEL and xp >= get_xp_threshold(server_level):
		print(get_xp_threshold(server_level))
		server_level += 1

	while server_level > 1 and xp < get_xp_threshold(server_level - 1):
		print(get_xp_threshold(server_level))
		server_level -= 1

	rows_affected = query_write(
		"""
			UPDATE servers
			SET server_level = ?
			WHERE server_id = ?
		""",
		(server_level, server_id),
	)

	return rows_affected > 0


async def get_server_status(server_id: int) -> ServerStats:
	s_level, s_xp, rank_cap = query_one(
		"""
			SELECT server_level, server_level_xp, rank_cap
			FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)

	s_xp_required = get_xp_threshold(s_level)

	return ServerStats(server_id, s_level, s_xp, s_xp_required, rank_cap)
