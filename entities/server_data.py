from dataclasses import dataclass

from shared_enums import LevelRewardType


@dataclass
class ServerStats:
	server_id: int
	level: int
	current_level_xp: int
	xp_required: int
	rank_cap: int
	total_xp: int


@dataclass
class LevelReward:
	type: LevelRewardType
	value: int | str
	desc: str


LEVEL_REWARDS: dict[int, list[LevelReward]] = {
	# Start at level 1.
	2: [LevelReward(LevelRewardType.RANK, 1, "Rank Cap Increased")],
	4: [LevelReward(LevelRewardType.RANK, 1, "Rank Cap Increased")],  # Temp Hold
	5: [LevelReward(LevelRewardType.SP_FUSION, "high_pixie_unlock", "Special Fusion for Fairy High Pixie")],
	8: [LevelReward(LevelRewardType.RANK, 1, "Rank Cap Increased")],  # Temp Hold
	10: [LevelReward(LevelRewardType.MISC, "faction_unlock", "Alignments and Factions Unlocked")],
}
