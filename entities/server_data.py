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
	r_type: LevelRewardType
	value: int | str
	desc: str


@dataclass
class LevelUpData:
	old_level: int
	new_level: int
	rewards: list[LevelReward]


LEVEL_REWARDS: dict[int, LevelReward] = {
	# Start at level 1.
	2: LevelReward(LevelRewardType.RANK, 1, "Rank Cap Increased"),
	4: LevelReward(LevelRewardType.RANK, 1, "Rank Cap Increased"),  # Temp Hold
	5: LevelReward(LevelRewardType.SP_FUSION_KEY, "sp_king_frost", "Special Fusion for Tyrant King Frost Unlocked"),
	8: LevelReward(LevelRewardType.RANK, 1, "Rank Cap Increased"),  # Temp Hold
	10: LevelReward(LevelRewardType.KEY, "faction_unlock", "Alignments and Factions Unlocked"),
}
