from entities.player_data import DemonEntry
from helpers.db import query_all, query_one, query_write
from shared_enums import DemonRegistration


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
		DemonRegistration: Enum indicating the demon's registration status. IN_PARTY, IN_COMP, UNREGISTERED.
	"""
	response = query_one(
		"""
			SELECT in_party FROM player_demons
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(user_id, server_id, demon_id),
	)[0]

	match response:
		case 1:
			return DemonRegistration.IN_PARTY
		case 2:
			return DemonRegistration.IN_COMP
		case _:
			return DemonRegistration.UNREGISTERED


async def check_party(user_id: int, server_id: int) -> list[dict]:
	"""
	Query the database for the player's current party. Joins the player_demons table with the demon database.

	Returns:
		list[dict]: List of demons in the player's party. Includes ID, name, race and stored_rank.
	"""
	# Retrieve the player's party.
	response = query_all(
		"""
			SELECT d.id, d.name, d.race, pd.stored_rank
			FROM player_demons pd
			JOIN demons d ON pd.demon_id = d.id
			WHERE pd.player_id = ? AND pd.server_id = ? AND pd.in_party = 1
			ORDER BY d.race ASC, d.id ASC
		""",
		(user_id, server_id),
	)

	return response if response else []


async def check_compendium(user_id: int, server_id: int) -> list[DemonEntry]:
	"""
	Query the database for the player's encountered demons. Joins the player_demons table with the demon database.

	Returns:
		list[DemonEntry]: List of demons in the player's compendium.
	"""

	# Use LEFT JOIN to get all demons. stored_rank will be NULL if player hasn't encountered them.
	rows = query_all(
		"""
			SELECT d.id, d.name, d.race, d.personality, pd.stored_rank, pd.in_party, d.gem
			FROM demons d
			LEFT JOIN player_demons pd ON pd.demon_id = d.id
				AND pd.player_id = ? AND pd.server_id = ?
			ORDER BY d.race ASC, d.id ASC
		""",
		(user_id, server_id),
	)

	entries = []
	for row in rows:
		demon_id, name, race, pers, rank, in_party, gem = row

		entries.append(
			DemonEntry(
				demon_id=demon_id,
				name=name,
				race=race,
				personality=pers,
				rank=rank,
				in_party=in_party,
				gem=gem,
			)
		)
	return entries


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


def get_selected_demon_id(player_id: int, server_id: int) -> int | None:
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
