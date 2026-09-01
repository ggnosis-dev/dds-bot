import asyncio
import random

import discord

from entities.demon_data import TOO_WEAK_LEEWAY, DemonData
from entities.encounter_data import JoinData, party_full_extra_responses
from entities.player_data import ENCOUNTER_WINDOW_HOURS
from helpers.messages import EncountersMsg
from queries import badge_queries, item_queries, player_demons_queries, player_queries, server_queries
from queries.currency_queries import update_mag
from queries.gem_queries import add_gem
from shared_enums import DemonRegistration, DupeReward


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

	Returns:
	    JoinData: Messages and responses to be passed on related to joining.
	"""
	server_id = server.id if server else None

	if server_id is None:
		raise RuntimeError("Server ID is None.")

	gems_to_add = 0
	gem_name = ""
	extra_response = None
	dupe_message = None
	party_stats = await player_demons_queries.get_party_stats(player.id, server_id)

	# Check if party's strongest member is TOO_WEAK.
	if party_stats.strongest < demon.rank - TOO_WEAK_LEEWAY:
		reg_status = DemonRegistration.TOO_WEAK

	else:
		reg_status = await player_demons_queries.check_demon_registration(player.id, server_id, demon.id)

		# If no room in party AND the demon isn't already in there, assign PARTY_FULL.
		if party_stats.size >= party_stats.cap and reg_status not in {
			DemonRegistration.IN_PARTY,
			DemonRegistration.ON_LOAN,
			DemonRegistration.LEADER,
		}:
			reg_status = DemonRegistration.PARTY_FULL

	match reg_status:
		case DemonRegistration.UNREGISTERED:
			# Add demon to COMP.
			asyncio.gather(
				player_demons_queries.add_demon_to_compendium(player.id, server_id, demon.id, demon.rank),
				player_demons_queries.set_demon_in_party(player.id, server_id, demon.id),
				player_demons_queries.update_party(player.id, server_id),
				player_demons_queries.update_party_average(player.id, server_id),
			)

			if party_stats.size < 1:
				await player_demons_queries.set_selected_demon(player.id, server_id, demon.id)

		case DemonRegistration.IN_COMP:
			# Only add demon to player's party, has been obtained before.
			asyncio.gather(
				player_demons_queries.set_demon_in_party(player.id, server_id, demon.id),
				player_demons_queries.update_party(player.id, server_id),
				player_demons_queries.update_party_average(player.id, server_id),
			)

		case DemonRegistration.IN_PARTY | DemonRegistration.ON_LOAN:
			# Add gem to player and increase MAG paid given the demon is already in the party.
			gems_to_add = _gems_for_rank(demon.rank)

			gem_name, dupe_message = await asyncio.gather(
				add_gem(player.id, server_id, demon.gems, gems_to_add),
				grant_dupe_reward(player.id, server_id, demon),
			)

		case DemonRegistration.PARTY_FULL:
			extra_response = party_full_extra_responses[demon.tone_type]
			gems_to_add = _gems_for_rank(demon.rank)
			gem_name = await add_gem(player.id, server_id, demon.gems, gems_to_add)

		case DemonRegistration.TOO_WEAK:
			extra_response = "TOO WEAK"

	race_mult, demon_mult = await asyncio.gather(
		player_queries.get_race_mag_mult(player.id, server_id, demon.race_id),
		player_demons_queries.get_demon_mag_mult(player.id, server_id, demon.id),
	)

	mag_mult = _get_mag_multipler(reg_status, race_mult, demon_mult)
	mag_to_add = int(demon.rank * 10 * mag_mult)
	await update_mag(player.id, server_id, mag_to_add)
	status_message = EncountersMsg.get_status_message(reg_status, demon, player.name, mag_to_add, gems_to_add, gem_name)

	return JoinData(
		status_message,
		extra_response,
		dupe_message,
	)


def _get_mag_multipler(reg_status: DemonRegistration, race_mult: float, demon_mult: float) -> float:
	"""Work out how much MAG to give to the player based on registration status, and various multipiers."""
	match reg_status:
		case DemonRegistration.IN_COMP | DemonRegistration.PARTY_FULL:
			reg_rate = 0.3
		case DemonRegistration.UNREGISTERED:
			reg_rate = 0.6
		case _:
			reg_rate = 0.9

	# (1 + 0) / 0.9 = 111
	# (1.1 + 0.05) / 0.9 = 128
	return (race_mult + demon_mult) / reg_rate


def _gems_for_rank(rank: int) -> int:
	"""When encounter is a demon player aleady has in party, gift 1 to 3 gems based on their rank."""
	# Always guaranteed 1.
	total = 1
	max_extra_gems = int(rank / 33)
	probability = 0.5

	for _ in range(max_extra_gems):
		if random.random() < probability:
			total += 1

	return total


async def get_num_available_for_encounters(server_id: int) -> int:
	"""Get numbers of demons available to be obtained in one single encounter."""
	player_count = await server_queries.get_player_count(server_id)

	if player_count > 10:
		demon_count = random.randint(2, 5)
	else:
		demon_count = random.randint(1, max(3, player_count // 2))

	return demon_count


async def grant_dupe_reward(
	summoner_id: int,
	server_id: int,
	demon: DemonData,
) -> str | None:

	mag_bonus = None

	# Do the update.
	new_dupe_level = await player_demons_queries.increase_dupe_level(summoner_id, server_id, demon.id)

	# Do more specific updates.
	match DupeReward(new_dupe_level):
		case DupeReward.COLOUR:
			await player_demons_queries.set_custom_colour_on_demon(summoner_id, server_id, demon.id)

		case DupeReward.RACE_MULT:
			mag_bonus = await player_queries.increase_race_mag_mult(summoner_id, server_id, demon.race_id)

		case DupeReward.GREETING:
			await player_demons_queries.set_custom_greeting_on_demon(summoner_id, server_id, demon.id)

		case DupeReward.GRIMOIRE:
			item_id = await item_queries.get_item_id_by_name("grimoire")
			if item_id is None:
				raise RuntimeError("Grimoire item returned None.")
			await item_queries.give_player_item(summoner_id, server_id, item_id)

		case DupeReward.BADGE:
			badge_id = await badge_queries.get_demon_badge_id(demon.id)
			if badge_id is None:
				raise RuntimeError("Badge for demon not available.")
			await badge_queries.set_badge_on_player(summoner_id, badge_id)

		case DupeReward.MAG_MULT | _:
			mag_bonus = await player_demons_queries.increase_demon_mag_mult(summoner_id, server_id, demon.id)

	response = EncountersMsg.get_dupe_message(new_dupe_level, demon.race, demon.name, mag_bonus)
	return response
