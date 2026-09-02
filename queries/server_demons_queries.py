from entities.comp_data import DemonEntry, ServerCompendiumDemon, convert_row_to_list_demon_entries
from helpers.db import query_all, query_one, query_write


async def _set_demon_on_loan(player_id: int, server_id: int, demon_id: int) -> None:
	"""Helper to set a demon to on_loan in the player's demons table."""
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


async def new_add_demon_to_server_compendium(player_id: int, server_id: int, demon_id: int) -> bool:
	# Release old loaned demon.
	await _release_demon_on_loan(server_id, demon_id)

	# Insert new demon and on conflict, update it instead.
	rows_affected = query_write(
		"""
				INSERT INTO server_demons (player_id, server_id, demon_id)
				VALUES (?, ?, ?)
				ON CONFLICT (server_id, demon_id) DO
					UPDATE SET player_id = excluded.player_id
				WHERE server_id = excluded.server_id
					AND demon_id = excluded.demon_id
			""",
		(player_id, server_id, demon_id),
	)

	# Set on loan for the player's demon.
	await _set_demon_on_loan(player_id, server_id, demon_id)

	return rows_affected > 0


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


# --------- CHECKS --------- #
async def get_serv_comp_demon(server_id: int, demon_id: int) -> ServerCompendiumDemon | None:
	"""Check for a single loaned demon. This is used for comparison checks such as overwriting an existing loaned demon."""
	row = query_one(
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

	if row is None:
		return None

	return ServerCompendiumDemon(
		server_id=row["server_id"],
		player_id=row["player_id"],
		demon_id=row["demon_id"],
		stored_rank=row["stored_rank"],
	)


async def check_server_compendium(server_id: int, owner_id: int | None = None, need_gems: bool = False) -> list[DemonEntry]:
	"""Retrieve list of the demons currently in the server COMP."""
	# If an owner_id is provided, we will only check WHERE that player's ID is found.
	params = (server_id, owner_id) if owner_id else (server_id,)
	show_only_owner = "WHERE sd.player_id = ?" if owner_id else ""

	rows = query_all(
		f"""
			SELECT d.id, d.name, r.name AS race, d.rank, d.tone, pd.stored_rank, pd.player_id AS owner_id
			FROM demons d
			JOIN races r ON d.race_id = r.id
			LEFT JOIN server_demons sd
				ON sd.demon_id = d.id
				AND sd.server_id = ?
			LEFT JOIN player_demons pd
				ON pd.player_id = sd.player_id
				AND pd.server_id = sd.server_id
				AND pd.demon_id = sd.demon_id
				{show_only_owner}
			ORDER BY race ASC, d.id ASC
		""",
		params,
	)

	return convert_row_to_list_demon_entries(rows, need_gems)
