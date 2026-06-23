from entities.server_data import LEVEL_REWARDS, LevelReward, ServerStats
from helpers.db import query_one, query_write
from shared_enums import LevelRewardType

"""
Server level:
	- Every time a demon is added to the Server COMP, add their rank to the XP.
	- If XP reaches a moving threshold, server levels up.
	- Have a list of perks to provide, right now we'll limit them just to rank cap increases.
"""

XP_START = 5
XP_END = 150
MAX_LEVEL = 10


# FIXME: Cleanup pleeeease


# https://gist.github.com/laundmo/b224b1f4c8ef6ca5fe47e132c8deab56
def get_xp_threshold(level: int) -> int:
	"""XP required to hit next level using a linear interpolate. Eases in due to the power of 2."""
	# level / (MAX_LEVEL - 1) ** 2
	# 9 / (9)^2 = 0.1111
	# 8 / (9)^2 = 0.0987
	# (level / (MAX_LEVEL - 1)) ** 2
	# (9 / (10 - 1))^2 = 1
	# (8 / (9))^2 = 0.79
	point_t = (level / MAX_LEVEL) ** 2
	xp_required = int((1 - point_t) + point_t * XP_END)
	return xp_required


async def try_server_level_up(server_id: int, rank: int) -> bool:
	print("INFO: try_server_level_up")
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

	old_level = server_level

	# Check to see if we are higher or lower than the threshold to next level.
	while server_level < MAX_LEVEL and xp >= get_xp_threshold(server_level + 1):
		server_level += 1

	while server_level > 1 and xp < get_xp_threshold(server_level):
		server_level -= 1

	print(server_level)
	# Exit early if there's no change in level.
	if server_level == old_level:
		return False

	query_write(
		"""
			UPDATE servers SET server_level = ?
			WHERE server_id = ?
		""",
		(server_level, server_id),
	)

	await _do_server_level_update(server_id, old_level, server_level)

	return True


async def get_rank_cap(server_id: int) -> int:
	response = query_one(
		"""
			SELECT rank_cap FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)[0]

	return response


async def get_server_status(server_id: int) -> ServerStats:
	s_level, s_xp, rank_cap = query_one(
		"""
			SELECT server_level, server_level_xp, rank_cap
			FROM servers
			WHERE server_id = ?
		""",
		(server_id,),
	)

	next_level_xp = get_xp_threshold(s_level + 1)

	# Level 1 should have 0 xp, don't try to calculate because we'll end up with negatives in next step.
	prev_level_xp = get_xp_threshold(s_level) if s_level > 1 else 0

	# Subtract the previous level requirement from the server XP to find how much they currently have towards the next level.
	current_level_xp = s_xp - prev_level_xp

	s_xp_required = next_level_xp - prev_level_xp

	return ServerStats(
		server_id=server_id,
		level=s_level,
		current_level_xp=current_level_xp,
		xp_required=s_xp_required,
		rank_cap=rank_cap,
		total_xp=s_xp,
	)


async def _do_server_level_update(server_id: int, old_level: int, new_level: int) -> None:
	print("DEBUG: Do server level update.")
	leveled_up = new_level > old_level

	if leveled_up:
		# for i in range is not inclusive of the final index. (1 + 1, 5 + 1) does [2, 3, 4, 5].
		levels_to_update = range(old_level + 1, new_level + 1)
	else:
		# -1 tells us to step backwards. (5, 1, -1) reverts levels [5, 4, 3, 2].
		levels_to_update = range(old_level, new_level, -1)

	for level in levels_to_update:
		# Use level 2 as default. This will do a standard rank cap increase.
		reward = LEVEL_REWARDS.get(level, LEVEL_REWARDS[2])
		print(f"DEBUG: Applying rank ({level}) reward to server: {server_id} | Reward is: {reward.r_type}.")
		await _apply_reward(server_id, reward, leveled_up)


async def _apply_reward(server_id: int, reward: LevelReward, level_up: bool) -> None:
	reverse = -1 if not level_up else 1

	match reward.r_type:
		case LevelRewardType.KEY | LevelRewardType.SP_FUSION_KEY:
			print("DEBUG: Applying key reward.")

			if level_up:
				query = "INSERT INTO server_unlocks (server_id, unlock_key) VALUES (?, ?)"
			else:
				query = "DELETE FROM server_unlocks WHERE server_id = ? AND unlock_key = ?"

			query_write(query, (server_id, reward.value))

		case LevelRewardType.RANK | _:
			print("DEBUG: Applying rank reward.")
			value = reward.value * reverse

			query_write(
				"""
					UPDATE servers
					SET rank_cap = rank_cap + ?
					WHERE server_id = ?
				""",
				(value, server_id),
			)
