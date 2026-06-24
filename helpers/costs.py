import random


def fusion_cost(demon_rank: int) -> int:
	return max(int(demon_rank * 100), 1000)


def summon_cost(demon_rank: int) -> int:
	return max(int(demon_rank * 100), 1000)


def daily_mag() -> int:
	return random.randint(100, 500)


def party_slot_cost(current_cap: int, number: int) -> int:
	unit = 500
	example = range(current_cap, current_cap + number)
	cost = unit * (current_cap - 10)

	for _ in example:
		cost += unit

	return cost
