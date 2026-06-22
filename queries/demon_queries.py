from numpy.random import triangular

from entities.demon_data import DemonData, convert_row_to_demon_data
from helpers.db import query_all, query_one


def get_demon_by_id(demon_id: int) -> DemonData | None:
	"""
	Retrieve a demon's data from the database using its unique ID.

	Args:
		demon_id (int): Identifier of the demon to retrieve data for.
	Returns:
		DemonData | None: Demon's data if found, otherwise None.
	"""
	row = query_one(
		"""
			SELECT id, name, race, rank, colour, personality, gem, image_url, profile_url
			FROM demons
			WHERE id = ?
		""",
		(demon_id,),
	)

	return convert_row_to_demon_data(row) if row else None


def get_demon_id_by_name(demon_name: str) -> int | None:
	"""Retrieve a demon's ID from the database using its name."""
	response = query_one(
		"""
			SELECT id FROM demons
			WHERE LOWER(name) = LOWER(?)
		""",
		(demon_name,),
	)[0]

	return response if response else None


def get_demon_by_name(demon_name: str) -> DemonData | None:
	"""Helper to get demon by name."""
	d_id = get_demon_id_by_name(demon_name)
	return get_demon_by_id(d_id) if d_id else None


def get_demon_name_by_id(demon_id: int) -> str:
	"""Retrieve a demon's name from the database using its ID."""
	response = query_one(
		"""
			SELECT name FROM demons
			WHERE id = ?
			""",
		(demon_id,),
	)[0]

	return response if response else ""


def get_random_demon() -> DemonData:
	"""Retrieve a random demon's data from the database. Does not need a profile."""
	row = query_one(
		"""
			SELECT * FROM demons
			ORDER BY RANDOM()
			LIMIT 1
		"""
	)

	if not row:
		raise RuntimeError("ERROR: No demons could be found in the database.")

	return convert_row_to_demon_data(row)


def get_demon_by_distribution(weighted_rank: int, max_rank: int) -> DemonData:
	try:
		weighted_rank = min(weighted_rank, max_rank)
		rank = round(triangular(left=0.5, mode=weighted_rank, right=max_rank + 0.5))
	except Exception as e:
		print(f"ERROR: {type(e)}: {e}")
		print(f"weighted_rank={weighted_rank}, max_rank={max_rank}")
		raise

	row = query_one(
		"""
			SELECT * FROM demons
			-- Order by proximity to rank. Then if a tie exists, order by random.
			ORDER BY ABS(rank - ?), RANDOM()
			-- Retrieve the top result.
			LIMIT 1
		""",
		(rank,),
	)

	if not row:
		raise RuntimeError("ERROR: No demons could be found in the database.")

	return convert_row_to_demon_data(row)


def get_demon_race_by_id(demon_id: int) -> str:
	"""Get demon's race from the database using its ID."""
	response = query_one(
		"""
			SELECT race FROM demons
			WHERE id = ?
		""",
		(demon_id,),
	)[0]

	return response


def get_demon_names_by_race(race: str) -> list[str]:
	"""Return a list of all demon names from  a race."""
	race = race.title()
	rows = query_all(
		"""
			SELECT name FROM demons
			WHERE race = ?
		""",
		(race,),
	)

	return [row[0] for row in rows]


def get_closest_demon_in_race(race: str, rank: int) -> DemonData | None:
	d_id = query_one(
		"""
			SELECT id FROM demons
			WHERE race = ?
			ORDER BY
				-- Order by absolute rank minus passed in rank.
				ABS(rank - ?),
				-- If there's a tie, prioritise the smaller one.
				rank
			LIMIT 1
		""",
		(race, rank),
	)[0]

	return get_demon_by_id(d_id)


def get_next_demon_in_race(race: str, rank: int, direction: int) -> DemonData | None:
	query = f"""
		SELECT id FROM demons
		WHERE race = ? AND rank {">" if direction == 1 else "<"} ?
	"""
	d_id = query_one(
		query,
		(race, rank),
	)[0]

	if d_id is None:
		return None

	return get_demon_by_id(d_id)
