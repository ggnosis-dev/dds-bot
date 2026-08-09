import random

import discord

from entities.demon_data import DemonData
from entities.player_data import ENCOUNTER_WINDOW_HOURS
from queries import player_demons_queries, server_queries
from queries.currency_queries import update_mag
from queries.gem_queries import add_gem, get_possible_gems
from shared_enums import DemonRegistration


def get_current_encounter_window(now: int) -> int:
	"""Get the current encounter window in seconds. Man, this took me way too long."""
	# Convert window hours to seconds.
	window_seconds = ENCOUNTER_WINDOW_HOURS * 3600

	# How many times the window has elapsed since the beginning.
	windows_elapsed = now // window_seconds

	# Take the number of windows elapsed and multiply it by how long a window takes in seconds.
	# We then know which window we're currently in.
	this_window = windows_elapsed * window_seconds

	return this_window


async def join_player_party(
	player: discord.User | discord.Member,
	server: discord.Guild | None,
	demon: DemonData,
) -> tuple[DemonRegistration, int, int, str]:
	"""
	Organises a demon to either be added to COMP, party or if it should give the player a gift
	instead.

	Args:
	    player (discord.User | discord.Member): Player to add the demon for.
	    server (discord.Guild | None): Server the player is in.
	    demon (DemonData): Demon's data to be added.
	Returns:
	    tuple[DemonRegistration, int, int]: Returns registration state the demon is in
			(IN_PARTY, IN_COMP, UNREGISTERED), amount of mag received and number of gems.
	"""
	server_id = server.id if server else None

	if server_id is None:
		raise RuntimeError("ERROR: Server ID is None.")

	mag_multiplier = 0
	gems_to_add = 0
	gem_name = ""
	party_stats = await player_demons_queries.get_party_stats(player.id, server_id)
	party_has_space = party_stats.size < party_stats.cap

	# Check if party has space before anything. If it doesn't, assign CANT_JOIN.
	if party_has_space:
		new_entry = await player_demons_queries.check_demon_registration(player.id, server_id, demon.id)
	else:
		new_entry = DemonRegistration.CANT_JOIN

	match new_entry:
		case DemonRegistration.UNREGISTERED:
			# Added demon to COMP with a little bonus MAG.
			mag_multiplier = 0.6
			await player_demons_queries.add_demon_to_compendium(player.id, server_id, demon.id, demon.rank)
			await player_demons_queries.set_demon_in_party(player.id, server_id, demon.id)
			await player_demons_queries.update_party_average(player.id, server_id)

			if party_stats.size < 1:
				player_demons_queries.set_selected_demon(player.id, server_id, demon.id)

		case DemonRegistration.IN_COMP:
			# Only add demon to player's party, has been obtained before.
			mag_multiplier = 0.3
			await player_demons_queries.set_demon_in_party(player.id, server_id, demon.id)
			await player_demons_queries.update_party_average(player.id, server_id)

		case DemonRegistration.IN_PARTY:
			# Add gem to player and increase MAG paid given the demon is already in the party.
			gems_to_add = _gems_for_rank(demon.rank)
			mag_multiplier = 0.9
			gem_name = await add_gem(player.id, server_id, demon.race, gems_to_add)

		case DemonRegistration.CANT_JOIN:
			gems_to_add = _gems_for_rank(demon.rank)
			mag_multiplier = 0.3
			gem_name = await add_gem(player.id, server_id, demon.race, gems_to_add)

	mag_to_add = int((demon.rank * 10) / mag_multiplier)
	update_mag(player.id, server_id, mag_to_add)

	return new_entry, mag_to_add, gems_to_add, gem_name


def _gems_for_rank(rank: int) -> int:
	"""
	When encounter is a demon player aleady has in party, gift them gems based on their rank.
	This should give them between 1 and 3.
	"""
	# Always guaranteed 1.
	total = 1
	max_extra_gems = int(rank / 33)

	# TODO: Thing we could let players manipulate.
	probability = 0.5

	for _ in range(max_extra_gems):
		if random.random() < probability:
			total += 1

	return total


async def get_count_for_encounters(server_id: int) -> int:
	player_count = await server_queries.get_player_count(server_id)

	if player_count > 10:
		demon_count = random.randint(2, 5)
	else:
		demon_count = random.randint(1, max(3, player_count // 2))

	return demon_count


def format_dialogue(message: str, demon_data: DemonData) -> str:
	if not message.startswith("[p]"):
		message = "-# **[name]**:\n-# " + message
	else:
		message.replace("[p]", "", 1)

	message = message.replace("[p]", "\n\n")
	message = message.replace("[d]", "\n\n-# **[name]**:\n-# ")
	message = message.replace("[race]", f"{demon_data.race.upper()}")
	message = message.replace("[name]", f"{demon_data.name.upper()}")

	if "[gem]" in message:
		gems = get_possible_gems(demon_data.race)
		message = message.replace("[gem]", f"{gems[0]}")

	return message
