from entities.comp_data import DemonEntry, ServerCompendiumDemon
from helpers.db import query_all, query_one, query_write


async def _set_demon_on_loan(player_id: int, server_id: int, demon_id: int) -> None:
	"""Helper to set a demon to on_loan."""
	query_write(
		"""
			UPDATE player_demons SET on_loan = 1
			WHERE player_id = ? AND server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)


async def _release_demon_on_loan(server_id: int, demon_id: int) -> None:
	"""Helper to release demon back to its owner and turn on_loan back to 0."""
	query_write(
		"""
			UPDATE player_demons SET on_loan = 0
			WHERE server_id = ? AND demon_id = ?
				AND player_id = (
					SELECT player_id FROM server_demons
					WHERE server_id = ? AND demon_id = ?
				)
		""",
		(server_id, demon_id, server_id, demon_id),
	)


async def add_demon_to_server_compendium(
	player_id: int,
	server_id: int,
	demon_id: int,
) -> bool:
	"""
	Add a demon to the server's compendium and mark it on loan.

	Args:
		player_id (int): Player ID.
		server_id (int): Server ID the player belongs to.
		demon_id (int): Demon's ID.
	Returns:
		bool: True if the demon was added, False if it already exists.
	"""
	# Check if demon is already in the server's COMP.
	exists_in_comp = query_one(
		"""
			SELECT 1 FROM server_demons
			WHERE server_id = ? AND demon_id = ?
		""",
		(server_id, demon_id),
	)

	# Return early if demon is already in compendium to avoid dupes.
	if exists_in_comp:
		return False

	# Insert reference to player's demon into the compendium.
	query_write(
		"""
			INSERT INTO server_demons (player_id, server_id, demon_id)
			VALUES (?, ?, ?)
		""",
		(player_id, server_id, demon_id),
	)

	# Update player's demon with the on loan flag.
	await _set_demon_on_loan(player_id, server_id, demon_id)

	return True


async def get_server_compendium_demon(server_id: int, demon_id: int) -> ServerCompendiumDemon:
	response = query_one(
		"""
			SELECT sd.*, pd.stored_rank FROM server_demons sd
			JOIN player_demons pd
				ON sd.player_id = pd.player_id
					AND sd.server_id = pd.server_id
					AND sd.demon_id = pd.demon_id
			WHERE sd.server_id = ? AND sd.demon_id = ?
		""",
		(server_id, demon_id),
	)

	pid, sid, did, rank = response
	return ServerCompendiumDemon(
		player_id=pid,
		server_id=sid,
		demon_id=did,
		stored_rank=rank,
	)


async def replace_server_compendium_demon(player_id: int, server_id: int, demon_id: int) -> None:
	"""Returns the original loaned demon to its original owner, then set new one."""
	# Release old loaned demon.
	await _release_demon_on_loan(server_id, demon_id)

	# Update compendium entry.
	query_write(
		"""
			UPDATE server_demons SET player_id = ?
			WHERE server_id = ? AND demon_id = ?
		""",
		(player_id, server_id, demon_id),
	)

	# Set on loan on demon.
	await _set_demon_on_loan(player_id, server_id, demon_id)


async def return_server_comp_demon(server_id: int, demon_id: int) -> bool:
	"""Returns the loaned demon and deletes entry from the server COMP."""
	# Set on loan back to 0.
	await _release_demon_on_loan(server_id, demon_id)

	# Delete the compendium entry.
	rows_affected = query_write(
		"""
			DELETE FROM server_demons
			WHERE server_id = ? AND demon_id = ?
		""",
		(server_id, demon_id),
	)

	return rows_affected > 0


async def check_server_compendium(server_id: int, owner_id: int | None = None) -> list[DemonEntry]:
	"""Retrieve list of the demons currently in the server COMP."""
	# If an owner_id is provided, we will only check WHERE that player's ID is found.
	params = (server_id, owner_id) if owner_id else (server_id,)
	show_only_owner = "WHERE sd.player_id = ?" if owner_id else ""

	rows = query_all(
		f"""
			SELECT d.id, d.name, d.race, d.personality, d.gem, pd.player_id, pd.stored_rank
			FROM demons d
			LEFT JOIN server_demons sd
				ON sd.demon_id = d.id
				AND sd.server_id = ?
			LEFT JOIN player_demons pd
				ON pd.player_id = sd.player_id
				AND pd.server_id = sd.server_id
				AND pd.demon_id = sd.demon_id
				{show_only_owner}
			ORDER BY d.race ASC, d.id ASC
		""",
		params,
	)

	entries = []
	for row in rows:
		did, name, race, pers, gem, oid, rank = row

		entries.append(
			DemonEntry(
				demon_id=did,
				owner_id=oid,
				name=name,
				race=race,
				personality=pers,
				rank=rank,
				gem=gem,
			)
		)
	return entries
