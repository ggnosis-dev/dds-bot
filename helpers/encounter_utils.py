from random import random

import discord

from entities.demon_data import DemonData
from entities.player_data import ENCOUNTER_WINDOW_HOURS
from queries import player_demons_queries
from queries.currency_queries import update_mag
from queries.gem_queries import add_gem
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
) -> tuple[DemonRegistration, int, int]:
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
	party_has_space = player_demons_queries.get_party_has_space(player.id, server_id)

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

		case DemonRegistration.IN_COMP:
			# Only add demon to player's party.
			mag_multiplier = 0.3
			await player_demons_queries.set_demon_in_party(player.id, server_id, demon.id)
			await player_demons_queries.update_party_average(player.id, server_id)

		case DemonRegistration.IN_PARTY | DemonRegistration.CANT_JOIN:
			# Add gem to player and increase MAG paid.
			gems_to_add = _gems_for_rank(demon.rank)
			mag_multiplier = 0.9
			await add_gem(player.id, server_id, demon.id, gems_to_add)

	mag_to_add = int((demon.rank * 10) / mag_multiplier)
	update_mag(player.id, server_id, mag_to_add)

	return new_entry, mag_to_add, gems_to_add


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
		if random() < probability:
			total += 1

	return total
