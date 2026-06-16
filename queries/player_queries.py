from discord.ext import commands

from entities.player_data import PlayerData
from helpers.db import query_one, query_write


# TODO: Really don't need to do this setup procedure.
async def setup_player(ctx: commands.Context) -> bool:
	"""
	Set up a new player in the database if they don't already have a profile.

	Returns:
		bool: True if a new profile was created, False if player already exists.
	"""
	if ctx.guild is None:
		raise RuntimeError(f"ERROR: Server ID could not be determined: {ctx}.")

	player_id = ctx.author.id
	server_id = ctx.guild.id

	if check_player_exists(player_id, server_id):
		await ctx.send("You already have a profile set up on this server!")
		return False

	await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")

	save_player_to_db(player_id, server_id)
	update_server_in_db(server_id)

	await ctx.send("Your profile has been set up!")

	return True


def save_player_to_db(player_id: int, server_id: int) -> bool:
	"""Save a new player's data to the database."""
	rows_affected = query_write(
		"""
			INSERT INTO players (player_id, server_id)
				VALUES (?, ?)
		""",
		(player_id, server_id),
	)
	print(f"INFO: New player added: {player_id} | Server {server_id}.")
	return rows_affected > 0


def update_server_in_db(server_id: int) -> bool:
	"""Update a server's data in the database."""
	rows_affected = query_write(
		"""
			INSERT INTO servers (server_id, player_count)
			VALUES (?, 1)
			ON CONFLICT (server_id) DO
				UPDATE SET player_count = player_count + 1
		""",
		(server_id,),
	)
	return rows_affected > 0


def check_player_exists(player_id, server_id) -> bool:
	"""
	Check if a player already exists in the database.

	Args:
		player_id (int): Player ID.
		player_server (int): Server ID the player belongs to.
	Returns:
		bool: True if the player exists, False otherwise.
	"""
	response = query_one(
		"""
			SELECT 1 FROM players
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	return response is not None


async def get_player(player_id, server_id) -> PlayerData | None:
	"""
	Get the properties of the player.

	Args:
		player_id (int): Player ID.
		server_id (int): Sever ID player belongs to.
	Returns:
		PlayerData: A data class of player properties.
	"""
	response = query_one(
		"""
			SELECT * FROM players
			WHERE player_id = ? AND server_id = ?
		""",
		(player_id, server_id),
	)

	if response is None:
		return None

	player_id, server_id, selected_demon_id, mag, p_size, p_cap, d_timer, e_timer = response

	return PlayerData(
		player_id=player_id,
		server_id=server_id,
		selected_demon_id=selected_demon_id,
		mag=mag,
		party_size=p_size,
		party_cap=p_cap,
		daily_timer=d_timer,
		encounter_timer=e_timer,
	)


async def set_daily_timer(player_id: int, server_id: int, time: int) -> bool:
	"""
	Set the player's daily timer.

	Returns:
		bool: True if successful, False otherwise.
	"""
	rows_affected = query_write(
		"""
			UPDATE players
			SET daily_timer = ?
			WHERE player_id = ? AND server_id = ?
		""",
		(time, player_id, server_id),
	)

	return rows_affected > 0


async def set_encounter_timer(player_id: int, server_id: int, time: int) -> bool:
	"""
	Set the player's encounter timer.

	Returns:
		bool: True if successful, False otherwise.
	"""
	rows_affected = query_write(
		"""
			UPDATE players
			SET encounter_timer = ?
			WHERE player_id = ? AND server_id = ?
		""",
		(time, player_id, server_id),
	)

	return rows_affected > 0
