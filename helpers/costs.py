import random


def fusion_cost(demon_rank: int) -> int:
	return max(int(demon_rank * 100), 1000)


def summon_cost(demon_rank: int) -> int:
	return max(int(demon_rank * 100), 1000)


def daily_mag() -> int:
	return random.randint(100, 500)
