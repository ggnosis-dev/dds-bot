from entities.comp_data import DemonEntry, convert_row_to_demon_entry
from entities.player_data import PartyStats
from helpers.db import query_all, query_one, query_write
from shared_enums import DemonRegistration


async def get_player_demon_by_id(player_id: int, server_id: int, demon_id: int) -> DemonEntry | None:
	row = query_all(
		"""
			SELECT d.id, d.name, d.race, d.rank, pd.on_loan, pd.stored_rank, pd.in_party
			FROM demons d
			JOIN player_demons pd ON pd.demon_id = d.id
				AND pd.player_id = ? AND pd.server_id = ?
			WHERE pd.demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	if row:
		d_id, name, race, rank, on_loan, st_rank, in_party = row[0]

		return DemonEntry(
			demon_id=d_id,
			name=name,
			race=race,
			initial_rank=rank,
			stored_rank=st_rank,
			on_loan=on_loan,
			in_party=in_party,
			owner_id=player_id,
		)
	return None


async def set_demon_in_party(player_id: int, server_id: int, demon_id: int, set_in_party: bool = True) -> bool:
	"""
	Manage whether to add or remove a demon from a player's party.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
		demon_id (int): Demon's ID.
		party_add (bool): True to add to party, False to remove from party.
	Returns:
		bool: True if the demon's status was updated, False otherwise.
	"""
	rows_affected = query_write(
		"""
			UPDATE player_demons
			SET in_party = ?
			WHERE player_id = ? AND server_id = ? AND demon_id = ? AND in_party != ?
		""",
		(set_in_party, player_id, server_id, demon_id, set_in_party),
	)

	add_remove = 1 if set_in_party else -1
	await update_party(player_id, server_id, add_remove)

	return rows_affected > 0


async def add_demon_to_compendium(player_id: int, server_id: int, demon_id: int, demon_rank: int) -> bool:
	"""
	Add a demon to the player's compendium if it doesn't already exist.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
		demon_id (int): Demon's ID.
		demon_rank (int): Demon's rank.
	Returns:
		bool: True if the demon was added, False if it already exists.
	"""

	# Check if demon is already in compendium.
	exists_in_comp = query_one(
		"""
			SELECT 1 FROM player_demons
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	# Return early if demon is already in compendium to avoid dupes.
	if exists_in_comp:
		return False

	query_write(
		"""
			INSERT INTO player_demons (player_id, server_id, demon_id, stored_rank, in_party)
			VALUES (?, ?, ?, ?, 0)
		""",
		(player_id, server_id, demon_id, demon_rank),
	)

	return True


async def check_demon_registration(user_id: int, server_id: int, demon_id: int) -> DemonRegistration:
	"""
	Check a demon's current state of registration for a specific player.

	Returns:
		DemonRegistration: Enum indicating the demon's registration status. IN_PARTY, IN_COMP, ON_LOAN, UNREGISTERED.
	"""
	response = query_one(
		"""
			SELECT in_party, on_loan FROM player_demons
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(user_id, server_id, demon_id),
	)

	if response is None:
		return DemonRegistration.UNREGISTERED

	in_party = response[0]
	on_loan = response[1]

	if on_loan:
		return DemonRegistration.ON_LOAN

	if in_party:
		return DemonRegistration.IN_PARTY
	return DemonRegistration.IN_COMP


async def check_party(user_id: int, server_id: int, need_gems: bool = False) -> list[DemonEntry]:
	"""
	Query the database for the player's current party. Joins the player_demons table with the demon database.

	Returns:
		list[dict]: List of demons in the player's party. Includes ID, name, race and stored_rank.
	"""
	rows = query_all(
		"""
			SELECT
				v.*,
				pd.on_loan,
				pd.stored_rank,
				pd.in_party
			FROM demon_entry_VIEW v
			JOIN player_demons pd ON pd.demon_id = v.id
				AND pd.player_id = ? AND pd.server_id = ?
			WHERE pd.in_party = 1
			ORDER BY v.race ASC, v.id ASC
		""",
		(user_id, server_id),
	)

	return convert_row_to_demon_entry(rows, need_gems)


async def get_player_demon_rank(player_id: int, server_id: int, demon_id: int) -> int:
	response = query_one(
		"""
			SELECT stored_rank FROM player_demons
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	return response[0] if response else -1


async def check_compendium(user_id: int, server_id: int, need_gems: bool = False) -> list[DemonEntry]:
	"""
	Query the database for the player's encountered demons. Joins the player_demons table with the demon database.

	Returns:
		list[DemonEntry]: List of demons in the player's compendium.
	"""
	# Use LEFT JOIN to get all demons. stored_rank will be NULL if player hasn't encountered them.
	rows = query_all(
		"""
			SELECT
				v.*,
				pd.on_loan,
				pd.stored_rank,
				pd.in_party
			FROM demon_entry_VIEW v
			LEFT JOIN player_demons pd ON pd.demon_id = v.id
				AND pd.player_id = ? AND pd.server_id = ?
			ORDER BY v.race ASC, v.id ASC
		""",
		(user_id, server_id),
	)

	return convert_row_to_demon_entry(rows, need_gems)


def set_selected_demon(player_id: int, server_id: int, demon_id: int) -> None:
	"""
	Set the selected demon for the player. The player's selected demon will hunt for their gem type,
	and have other uses in the future.
	"""
	query_write(
		"""
			UPDATE players
			SET selected_demon_id = ?
			WHERE player_id = ? AND server_id = ?
		""",
		(demon_id, player_id, server_id),
	)


async def get_selected_demon_id(player_id: int, server_id: int) -> int | None:
	"""
	Get the player's selected demon ID.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
	Returns:
		int | None: The selected demon's ID if it exists, otherwise None.
	"""
	response = query_one(
		"""
			SELECT selected_demon_id FROM players
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)[0]

	return response if response else None


async def update_party(player_id: int, server_id: int, party_add: int = 1) -> bool:
	"""
	Add or subract to the player's current party count.

	Returns:
		bool: True if successful, False otherwise.
	"""
	# If adding to party, we will only allow if party_size < party_cap.
	# If removing from party, need to make sure we have one left.
	if party_add > 0:
		where = "WHERE party_size < party_cap"
	else:
		where = "WHERE party_size > 1"

	rows_affected = query_write(
		f"""
			UPDATE players
			SET party_size = party_size + ?
			{where}
				AND player_id = ?
				AND server_id = ?
		""",
		(party_add, player_id, server_id),
	)

	if rows_affected == 0:
		raise RuntimeError("ERROR: Attempted Party size updated. Shouldn't have reached this hence missing a check.")

	return rows_affected > 0


def get_party_has_space(player_id: int, server_id: int) -> bool:
	"""
	Check if the player's party is full.

	Returns:
		bool: True if has space, False otherwise.
	"""
	response = query_one(
		"""
			SELECT 1 FROM players
			WHERE party_size < party_cap
				AND player_id = ?
				AND server_id = ?
		""",
		(player_id, server_id),
	)

	return response is not None


async def calculate_party_average(player_id: int, server_id: int) -> int:
	# print("DEBUG: calculate_party_average")
	party = await check_party(player_id, server_id)
	ranks = []

	# Isolate rank.
	for demon in party:
		ranks.append(demon.stored_rank)

	average = max(1, sum(ranks) // len(ranks))

	return average


async def update_party_average(player_id: int, server_id: int) -> bool:
	# print("DEBUG: update_party_average")
	average_rank = await calculate_party_average(player_id, server_id)

	rows_affected = query_write(
		"""
			UPDATE players
			SET party_average_rank = ?
			WHERE player_id = ?
				AND server_id = ?
		""",
		(average_rank, player_id, server_id),
	)

	return rows_affected > 0


async def get_party_average(player_id: int, server_id: int) -> int:
	response = query_one(
		"""
			SELECT party_average_rank FROM players
			WHERE player_id = ?
				AND server_id = ?
		""",
		(player_id, server_id),
	)[0]

	return max(1, response)


async def get_party_stats(player_id: int, server_id: int) -> PartyStats:
	size, cap, average = query_one(
		"""
			SELECT party_size, party_cap, party_average_rank FROM players
			WHERE player_id = ?
				AND server_id = ?
		""",
		(player_id, server_id),
	)

	strongest = await get_strongest_party_demon_rank(player_id, server_id)

	return PartyStats(size=size, cap=cap, average=average, strongest=strongest)


async def get_strongest_party_demon_rank(player_id: int, server_id: int) -> int:
	# Because we're doing MAX, we will always get a valid response object.
	response = query_one(
		"""
			SELECT MAX(stored_rank) FROM player_demons
			WHERE player_id = ? AND server_id = ? AND in_party = 1
		""",
		(player_id, server_id),
	)[0]

	return response if response is not None else 1
