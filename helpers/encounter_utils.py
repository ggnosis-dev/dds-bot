import asyncio
import random

import discord

from entities.demon_data import TOO_WEAK_LEEWAY, DemonData
from entities.encounter_data import JoinData, party_full_extra_responses
from entities.player_data import ENCOUNTER_WINDOW_HOURS
from queries import badge_queries, item_queries, player_demons_queries, player_queries, server_queries
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
) -> JoinData:
	"""
	Organises a demon to either be added to COMP, party or if it should give the player a gift
	instead.

	Args:
	    player (discord.User | discord.Member): Player to add the demon for.
	    server (discord.Guild | None): Server the player is in.
	    demon (DemonData): Demon's data to be added.
	Returns:
	    JoinData: Data to be passed on related to joining.
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
		new_entry = DemonRegistration.TOO_WEAK

	# Check if party has space after the TOO_WEAK check. If it doesn't, assign PARTY_FULL.
	elif party_stats.size < party_stats.cap:
		new_entry = await player_demons_queries.check_demon_registration(player.id, server_id, demon.id)
	else:
		new_entry = DemonRegistration.PARTY_FULL

	match new_entry:
		case DemonRegistration.UNREGISTERED:
			# Add demon to COMP.
			asyncio.gather(
				player_demons_queries.add_demon_to_compendium(player.id, server_id, demon.id, demon.rank),
				player_demons_queries.set_demon_in_party(player.id, server_id, demon.id),
				player_demons_queries.update_party_average(player.id, server_id),
			)

			if party_stats.size < 1:
				player_demons_queries.set_selected_demon(player.id, server_id, demon.id)

		case DemonRegistration.IN_COMP:
			# Only add demon to player's party, has been obtained before.
			asyncio.gather(
				player_demons_queries.set_demon_in_party(player.id, server_id, demon.id),
				player_demons_queries.update_party_average(player.id, server_id),
			)

		case DemonRegistration.IN_PARTY | DemonRegistration.ON_LOAN:
			# Add gem to player and increase MAG paid given the demon is already in the party.
			gems_to_add = _gems_for_rank(demon.rank)

			gem_name, dupe_message = await asyncio.gather(
				add_gem(player.id, server_id, demon.race, gems_to_add),
				grant_dupe_reward(player.id, server_id, demon),
			)

		case DemonRegistration.PARTY_FULL:
			extra_response = party_full_extra_responses[demon.tone_type]
			gems_to_add = _gems_for_rank(demon.rank)

			gem_name, dupe_message = await asyncio.gather(
				add_gem(player.id, server_id, demon.race, gems_to_add),
				grant_dupe_reward(player.id, server_id, demon),
			)

		case DemonRegistration.TOO_WEAK:
			extra_response = "TOO WEAK"

	mag_mult = _get_mag_multipler(player.id, server_id, demon, new_entry)
	mag_to_add = int(demon.rank * 10 * mag_mult)
	update_mag(player.id, server_id, mag_to_add)
	status_message = _get_status_message(new_entry, demon, player.name, mag_to_add, gems_to_add, gem_name)

	return JoinData(
		status_message,
		extra_response,
		dupe_message,
	)


def _get_mag_multipler(player_id: int, server_id: int, demon: DemonData, reg_status: DemonRegistration) -> float:
	race_mult = player_queries.get_race_mag_mult(player_id, server_id, demon.race_id)
	demon_mult = player_demons_queries.get_demon_mag_mult(player_id, server_id, demon.id)

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


def _get_status_message(new_entry, demon, user_name, mag_received, gems_added, gem_name) -> str:
	match new_entry:
		# Brand new demon.
		case DemonRegistration.UNREGISTERED:
			status = f"> {demon.race} {demon.name} was registered to {user_name}'s compendium! +{mag_received} MAG"

		# Demon will join the party but has already been registered before.
		case DemonRegistration.IN_COMP:
			status = f"> {demon.race} {demon.name} has joined {user_name}'s party! +{mag_received} MAG"

		# Demon already in the party.
		case DemonRegistration.IN_PARTY | DemonRegistration.ON_LOAN:
			status_addition = "| +0.05x Mult" if demon.dupes >= 5 else ""

			status = (
				f"> {demon.race} {demon.name} gifted {user_name} {gems_added} {gem_name.title()}!"
				f" +{mag_received} MAG {status_addition}"
			)

		# Party had too many demons already.
		case DemonRegistration.PARTY_FULL:
			status = (
				f"> {demon.race} {demon.name} could not join {user_name}. Party was full!"
				f" +{gems_added} {gem_name.title()}! +{mag_received} MAG"
			)

		# Player was too weak to control the demon.
		case DemonRegistration.TOO_WEAK | _:
			status = f"> {demon.race} {demon.name} did not join {user_name}. They were too weak! +{mag_received} MAG"

	return status


def _gems_for_rank(rank: int) -> int:
	"""
	When encounter is a demon player aleady has in party, gift them gems based on their rank.
	This should give them between 1 and 3.
	"""
	# Always guaranteed 1.
	total = 1
	max_extra_gems = int(rank / 33)
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


async def grant_dupe_reward(summoner_id: int, server_id: int, demon: DemonData) -> str | None:
	# Do the update.
	await player_demons_queries.increase_dupe_level(summoner_id, server_id, demon.id)

	# Get a response if needed.
	response = None
	dupe_level = demon.dupes + 1

	match dupe_level:
		case 1:
			await player_demons_queries.set_custom_colour_on_demon(summoner_id, server_id, demon.id)
			response = (
				f"You have unlocked the ability to customise the side colour for your **{demon.name}**"
				" (see `>demon_colour`)!"
			)
		case 2:
			await player_queries.increase_race_mag_mult(summoner_id, server_id, demon.race_id)
			race_bonus = player_queries.get_race_mag_mult(summoner_id, server_id, demon.race_id)
			response = (
				f"**{demon.name}** has contributed +0.1x to **{demon.race}'s MAG Multiplier**!"
				f" Any MAG received from the **{demon.race}** race will now be multiplied by **{race_bonus}**!"
			)
		case 3:
			await player_demons_queries.set_custom_greeting_on_demon(summoner_id, server_id, demon.id)
			response = (
				f"You have unlocked the ability to customise the greeting for your **{demon.name}** (see `>set_greeting`)!"
			)
		case 4:
			item_id = item_queries.get_item_id_by_name("grimoire")
			if item_id is None:
				raise RuntimeError("Grimoire item returned None.")
			item_queries.give_player_item(summoner_id, server_id, item_id)
			response = f"**{demon.name}** has gifted you a special item: **Grimoire**!"
		case 5:
			badge_id = badge_queries.get_demon_badge_id(demon.id)
			if badge_id is None:
				raise RuntimeError("Badge for demon not available.")
			badge_queries.set_badge_on_player(summoner_id, badge_id)
			response = (
				f"You are now fully linked with **{demon.name}**!"
				" A universal badge has been added to your player (see `>badges`)!"
				f"\n\n-# Any levels after this will add **+0.05x MAG multiplier** when interacting with **{demon.name}**."
			)
		case _:
			await player_demons_queries.increase_demon_mag_mult(summoner_id, server_id, demon.id)

	return response
