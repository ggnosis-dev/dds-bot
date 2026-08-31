from numpy.random import triangular

from entities.demon_data import DemonData, DesignData, convert_row_to_demon_data, convert_row_to_design_data
from helpers.db import query_all, query_one


async def get_demon_by_id(player_id: int, server_id: int, demon_id: int) -> DemonData:
	"""
	Retrieve a demon's data from the database using its unique ID.

	Args:
		player_id (int): Used to get certain custom design data.
		server_id (int): Same as above.
		demon_id (int): Identifier of the demon to retrieve data for.
	Returns:
		DemonData | None: Demon's data if found, otherwise None.
	"""
	row = query_one(
		"""
			SELECT
				v.*,
				pd.dupes,
				pd.colour,
				pd.greeting
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON pd.demon_id = v.id
				AND pd.player_id = ?
				AND pd.server_id = ?
			WHERE v.id = ?
		""",
		(player_id, server_id, demon_id),
	)

	if row is None:
		raise RuntimeError("Provided demon_id was out of bounds.")

	return convert_row_to_demon_data(row)


async def get_demon_id_by_name(demon_name: str) -> int | None:
	"""Retrieve a demon's ID from the database using its name."""
	response = query_one(
		"""
			SELECT id FROM demons
			WHERE LOWER(name) = LOWER(?)
		""",
		(demon_name,),
	)

	return response[0] if response else None


async def get_demon_by_name(player_id: int, server_id: int, demon_name: str) -> DemonData | None:
	"""Helper to get demon by name."""
	d_id = await get_demon_id_by_name(demon_name)
	return await get_demon_by_id(player_id, server_id, d_id) if d_id else None


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


async def get_random_demon() -> DemonData:
	"""
	Retrieve a random demon's data from the database. Does not need a profile.
	Used mainly for testing.
	"""
	row = query_one(
		"""
			SELECT
				v.*,
				pd.dupes,
				pd.colour,
				pd.greeting
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON pd.demon_id = v.id
				AND pd.player_id = 0
				AND pd.server_id = 0
			ORDER BY RANDOM()
			LIMIT 1
		"""
	)

	if not row:
		raise RuntimeError("ERROR: No demons could be found in the database.")

	return convert_row_to_demon_data(row)


async def get_demon_by_distribution(
	player_id: int,
	server_id: int,
	weighted_rank: int,
	max_rank: int,
) -> DemonData:
	try:
		weighted_rank = min(weighted_rank, max_rank)
		rank = round(triangular(left=0.5, mode=weighted_rank, right=max_rank + 0.5))
	except Exception as e:
		print(f"ERROR: demon_queries.py | get_demon_by_distribution | {type(e)}: {e}")
		print(f"weighted_rank={weighted_rank}, max_rank={max_rank}")
		raise

	row = query_one(
		"""
			SELECT
				v.*,
				pd.dupes,
				pd.colour,
				pd.greeting
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON pd.demon_id = v.id
				AND pd.player_id = ?
				AND pd.server_id = ?
			WHERE prevent_spawn = 0
				AND rank <= ?
			-- Order by proximity to rank. Then if a tie exists, order by random.
			ORDER BY ABS(rank - ?), RANDOM()
			-- Retrieve the top result.
			LIMIT 1
		""",
		(player_id, server_id, max_rank, rank),
	)

	if not row:
		raise RuntimeError("ERROR: No demons could be found in the database.")

	return convert_row_to_demon_data(row)


def get_demon_race_by_id(demon_id: int) -> str:
	"""Get demon's race from the database using its ID."""
	response = query_one(
		"""
			SELECT r.name FROM demons d
			JOIN races r ON d.race_id = r.id
			WHERE d.id = ?
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


async def get_design_data(demon_id: int, player_id: int = 0, server_id: int = 0) -> DesignData:
	"""player_id and server_id are optional. Without them, default colour should be provided."""
	row = query_one(
		"""
			SELECT d.profile_img, d.encounter_img, pd.colour, pd.greeting
			FROM demons d
			LEFT JOIN player_demons pd
				ON d.id = pd.demon_id
				AND pd.player_id = ?
				AND pd.server_id = ?
			WHERE d.id = ?
		""",
		(player_id, server_id, demon_id),
	)

	return convert_row_to_design_data(row)
