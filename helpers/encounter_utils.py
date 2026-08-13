import asyncio
import random

import discord

from entities.demon_data import DemonData
from entities.encounter_data import JoinData, party_full_extra_responses
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
) -> JoinData:
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
	extra_response = None
	party_stats = await player_demons_queries.get_party_stats(player.id, server_id)

	# Check if party's strongest member is TOO_WEAK.
	if party_stats.strongest > demon.rank + 3:
		new_entry = DemonRegistration.TOO_WEAK

	# Check if party has space after the TOO_WEAK check. If it doesn't, assign PARTY_FULL.
	elif party_stats.size < party_stats.cap:
		new_entry = await player_demons_queries.check_demon_registration(player.id, server_id, demon.id)
	else:
		new_entry = DemonRegistration.PARTY_FULL

	match new_entry:
		case DemonRegistration.UNREGISTERED:
			# Added demon to COMP with a little bonus MAG.
			mag_multiplier = 0.6
			asyncio.gather(
				player_demons_queries.add_demon_to_compendium(player.id, server_id, demon.id, demon.rank),
				player_demons_queries.set_demon_in_party(player.id, server_id, demon.id),
				player_demons_queries.update_party_average(player.id, server_id),
			)

			if party_stats.size < 1:
				player_demons_queries.set_selected_demon(player.id, server_id, demon.id)

		case DemonRegistration.IN_COMP:
			# Only add demon to player's party, has been obtained before.
			mag_multiplier = 0.3
			asyncio.gather(
				player_demons_queries.set_demon_in_party(player.id, server_id, demon.id),
				player_demons_queries.update_party_average(player.id, server_id),
			)

		case DemonRegistration.IN_PARTY:
			# Add gem to player and increase MAG paid given the demon is already in the party.
			gems_to_add = _gems_for_rank(demon.rank)
			mag_multiplier = 0.9
			gem_name = await add_gem(player.id, server_id, demon.race, gems_to_add)

		case DemonRegistration.PARTY_FULL:
			gems_to_add = _gems_for_rank(demon.rank)
			mag_multiplier = 0.3
			gem_name = await add_gem(player.id, server_id, demon.race, gems_to_add)
			extra_response = party_full_extra_responses[demon.tone_type]

		case DemonRegistration.TOO_WEAK:
			mag_multiplier = 0.1
			extra_response = "TOO WEAK"

	mag_to_add = int((demon.rank * 10) / mag_multiplier)
	update_mag(player.id, server_id, mag_to_add)
	status_message = _get_status_message(new_entry, demon, player.name, mag_to_add, gems_to_add, gem_name)

	return JoinData(
		new_entry,
		status_message,
		extra_response,
	)


def _get_status_message(new_entry, demon, user_name, mag_received, gems_added, gem_name) -> str:
	match new_entry:
		case DemonRegistration.UNREGISTERED:
			status = f"> {demon.race} {demon.name} was registered to {user_name}'s compendium! +{mag_received} MAG"

		case DemonRegistration.IN_COMP:
			status = f"> {demon.race} {demon.name} has joined {user_name}'s party! +{mag_received} MAG"

		case DemonRegistration.IN_PARTY:
			status = f"> {demon.race} {demon.name} gifted {user_name} {gems_added} {gem_name.title()}! +{mag_received} MAG"

		case DemonRegistration.PARTY_FULL:
			status = (
				f"> {demon.race} {demon.name} could not join {user_name} as party was full."
				f" {gems_added} {gem_name.title()}! +{mag_received} MAG"
			)

		case DemonRegistration.TOO_WEAK | _:
			status = f"> {demon.race} {demon.name} did not join {user_name} as they were too weak. +{mag_received} MAG"

	return status


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
