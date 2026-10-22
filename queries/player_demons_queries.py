from time import time

from entities.comp_data import DemonTableRow, convert_row_to_demon_table_row, convert_row_to_demon_table_rows
from entities.demon_data import DEFAULT_DEMON_MULT_INCREMENT, GREETING_LENGTH
from helpers.db import query_all, query_one, query_write
from shared_enums import DemonRegistration


async def get_player_demon_by_id(player_id: int, demon_id: int) -> DemonTableRow | None:
	"""Get a player's demon data by its ID."""

	row = query_one(
		"""
			SELECT
				v.*,
				pd.on_loan,
				pd.stored_rank,
				pd.in_party,
				pd.dupes
			FROM demon_entry_VIEW v
			JOIN player_demons pd ON pd.demon_id = v.id
			WHERE pd.player_id = ? AND pd.demon_id = ?
		""",
		(player_id, demon_id),
	)
	return convert_row_to_demon_table_row(row) if row else None


async def set_demon_in_party(player_id: int, demon_id: int, set_in_party: bool = True) -> bool:
	"""
	Manage whether to add or remove a demon from a player's party.

	Args:
		party_add (bool): True to add to party, False to remove from party.
	Returns:
		bool: True if the demon's status was updated, False otherwise.
	"""

	rows_affected = query_write(
		"""
			UPDATE player_demons
			SET in_party = ?
			WHERE player_id = ? AND demon_id = ? AND in_party != ?
		""",
		(set_in_party, player_id, demon_id, set_in_party),
	)

	return rows_affected > 0


async def add_demon_to_compendium(player_id: int, demon_id: int, demon_rank: int) -> bool:
	"""
	Add a demon to the player's compendium if it doesn't already exist.

	Returns:
		bool: True if the demon was added, False if it already exists.
	"""

	# Check if demon is already in compendium.
	exists_in_comp = query_one(
		"""
			SELECT 1 FROM player_demons
			WHERE player_id = ? AND demon_id = ?
		""",
		(player_id, demon_id),
	)

	# Return early if demon is already in compendium to avoid dupes.
	if exists_in_comp:
		return False

	query_write(
		"""
			INSERT INTO player_demons (player_id, demon_id, stored_rank, in_party, date_met)
			VALUES (?, ?, ?, 0, ?)
		""",
		(player_id, demon_id, demon_rank, int(time())),
	)

	return True


async def check_demon_registration(player_id: int, demon_id: int) -> DemonRegistration:
	"""
	Check a demon's current state of registration for a specific player.

	Returns:
		DemonRegistration: Enum indicating the demon's registration status. IN_PARTY, IN_COMP, ON_LOAN, LEADER, UNREGISTERED.
	"""

	row = query_one(
		"""
			SELECT pd.in_party, pd.on_loan, p.selected_demon_id
			FROM player_demons pd
			JOIN players p ON p.player_id = pd.player_id
			WHERE pd.player_id = ? AND pd.demon_id = ?
		""",
		(player_id, demon_id),
	)

	if row is None:
		return DemonRegistration.UNREGISTERED

	if row["selected_demon_id"] == demon_id:
		return DemonRegistration.LEADER

	if row["on_loan"]:
		return DemonRegistration.ON_LOAN

	if row["in_party"]:
		return DemonRegistration.IN_PARTY

	return DemonRegistration.IN_COMP


async def check_party(player_id: int, need_gems: bool = False) -> list[DemonTableRow]:
	"""
	Query the database for the player's current party. Joins the player_demons table with the demon database.

	Args:
		need_gems (bool): Default False. Set True if gem column is needed which will assign gems using a cache method.
	Returns:
		list[dict]: List of demons in the player's party. Includes ID, name, race and stored_rank.
	"""

	rows = query_all(
		"""
			SELECT
				v.*,
				pd.on_loan,
				pd.stored_rank,
				pd.in_party,
				pd.dupes
			FROM demon_entry_VIEW v
			JOIN player_demons pd ON pd.demon_id = v.id
				AND pd.player_id = ?
			WHERE pd.in_party = 1
			ORDER BY v.race ASC, v.id ASC
		""",
		(player_id,),
	)

	return await convert_row_to_demon_table_rows(rows, need_gems)


async def get_player_demon_rank(player_id: int, demon_id: int) -> int:
	"""Get a stored demon's rank, mainly for use when hunting gems."""
	row = query_one(
		"""
			SELECT stored_rank FROM player_demons
			WHERE player_id = ? AND demon_id = ?
		""",
		(player_id, demon_id),
	)

	return row[0] if row else -1


async def check_compendium(player_id: int, need_gems: bool = False) -> list[DemonTableRow]:
	"""
	Query the database for the player's encountered demons. Joins the player_demons table with the demon database.

	Args:
		need_gems (bool): Default False. Set True if gem column is needed which will assign gems using a cache method.
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
				pd.in_party,
				pd.dupes
			FROM demon_entry_VIEW v
			LEFT JOIN player_demons pd ON pd.demon_id = v.id
				AND pd.player_id = ?
			ORDER BY v.race ASC, v.id ASC
		""",
		(player_id,),
	)

	return await convert_row_to_demon_table_rows(rows, need_gems)


async def get_demon_entries(player_id: int) -> list[int]:
	"""
	Query database for a list of IDs that the player has encountered.

	Returns:
		list[int]: List of demon IDs in the player's compendium.
	"""

	rows = query_all(
		"""
			SELECT pd.demon_id FROM player_demons pd
			JOIN demons d ON pd.demon_id = d.id
			JOIN races r ON d.race_id = r.id
			WHERE pd.player_id = ?
			ORDER BY r.name ASC, d.rank ASC
		""",
		(player_id,),
	)

	entry_ids = [row["demon_id"] for row in rows]
	return entry_ids


async def set_selected_demon(player_id: int, demon_id: int) -> None:
	"""
	Set the selected demon for the player. The player's selected demon will hunt for their gem type,
	and have other uses in the future.
	"""

	query_write(
		"""
			UPDATE players
			SET selected_demon_id = ?
			WHERE player_id = ?
		""",
		(demon_id, player_id),
	)


async def get_selected_demon_id(player_id: int) -> int | None:
	"""
	Get the player's selected demon ID.

	Returns:
		int | None: The selected demon's ID if it exists, otherwise None.
	"""

	row = query_one(
		"""
			SELECT selected_demon_id FROM players
			WHERE player_id = ?
		""",
		(player_id,),
	)
	return row[0] if row else None


async def increase_dupe_level(player_id: int, demon_id: int) -> int:
	"""Add a level when a duplicate demon is encountered by the player."""

	row = query_one(
		"""
			UPDATE player_demons
			SET dupes = dupes + 1
			WHERE player_id = ?
				AND demon_id = ?
			RETURNING dupes
		""",
		(player_id, demon_id),
	)

	if row is None:
		raise RuntimeError("increase_dupe_level was called for an invalid player demon.")
	return row[0]


async def set_custom_colour_on_demon(player_id: int, demon_id: int, colour: int = 0) -> bool:
	"""When setting colour to 0, it will still hit the OR check in demon_data, thus becoming DEFAULT again."""

	rows_affected = query_write(
		"""
			UPDATE player_demons
			SET colour = ?
			WHERE player_id = ?
				AND demon_id = ?
		""",
		(colour, player_id, demon_id),
	)

	return rows_affected > 0


async def get_custom_colour_on_demon(player_id: int, demon_id: int) -> int | None:
	"""If colour is not NULL or None, it means that the player has it unlocked for the demon."""

	row = query_one(
		"""
			SELECT colour FROM player_demons
			WHERE player_id = ?
				AND demon_id = ?
		""",
		(player_id, demon_id),
	)
	return row[0] if row else None


async def set_custom_greeting_on_demon(player_id: int, demon_id: int, greeting: str = "") -> bool:
	"""Update what the demon will say when it is encountered."""

	if len(greeting) > GREETING_LENGTH:
		# Too long. SQLite doesn't have a way to validate text length so has to be done here.
		return False

	rows_affected = query_write(
		"""
			UPDATE player_demons
			SET greeting = ?
			WHERE player_id = ?
				AND demon_id = ?
		""",
		(greeting, player_id, demon_id),
	)
	return rows_affected > 0


async def get_custom_greeting_on_demon(player_id: int, demon_id: int) -> str | None:
	"""If greeting is NOT NULL/None, it implies that the player has it unlocked for the demon."""

	row = query_one(
		"""
			SELECT greeting FROM player_demons
			WHERE player_id = ?
				AND demon_id = ?
		""",
		(player_id, demon_id),
	)
	return row[0] if row else None


async def increase_demon_mag_mult(
	player_id: int,
	demon_id: int,
	amount: float = DEFAULT_DEMON_MULT_INCREMENT,
) -> float:
	"""Update and return the MAG multiplier value."""

	row = query_one(
		"""
			UPDATE player_demons
			SET mag_mult = mag_mult + ?
			WHERE player_id = ?
				AND demon_id = ?
			RETURNING mag_mult
		""",
		(amount, player_id, demon_id),
	)
	return row[0]


async def get_demon_mag_mult(player_id: int, demon_id: int) -> float:
	"""Retrieve the demon specific MAG multiplier if it exists."""

	row = query_one(
		"""
			SELECT mag_mult FROM player_demons
			WHERE player_id = ?
				AND demon_id = ?
		""",
		(player_id, demon_id),
	)
	return row[0] if row else 1.0
