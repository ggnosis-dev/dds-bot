from random import choice

from entities.badge_data import BadgeData
from entities.command_data import CommandData
from entities.demon_data import DEFAULT_DEMON_MULT_INCREMENT, DEFAULT_RACE_MULT_INCREMENT, DemonData
from entities.fusion_data import IngredientData
from entities.server_data import ServerStats
from helpers import format_utils
from shared_enums import DemonRegistration, DupeReward, Emotes, Unicode


class GenericMsg:
	@staticmethod
	def not_in_party(demon_name: str) -> str:
		if not demon_name:
			demon_name = "Demon"
		return f"**{demon_name.title()}** could not be found in your party..."

	@staticmethod
	def not_in_comp(demon_name: str) -> str:
		if not demon_name:
			demon_name = "Demon"
		return f"The demon **{demon_name.title()}** was not found in your compendium."

	@staticmethod
	def currently_on_loan(demon_name: str) -> str:
		return f"**{demon_name}** is currently being loaned to the Server Compendium..."

	@staticmethod
	def currently_leader(demon_name: str) -> str:
		return f"**{demon_name}** is currently set as your leader. Use `>leader {{demon}}` to change your leader."

	@staticmethod
	def no_leader() -> str:
		return "There is no demon leading your party. Select one using `>leader {name}`."

	@staticmethod
	def party_full() -> str:
		return "Your party is full! You can increase capacity using `>increase_party`."

	@staticmethod
	def already_in_party() -> str:
		return "You already have this demon in your party..."

	@staticmethod
	def no_input_given(command: CommandData) -> str:
		return f"### `> DDS-BOT HELP SYSTEM` {Emotes.HUH.value}\n{command.help}\n\n-# `{command.usage}`"

	@staticmethod
	def registered_to_compendium(race: str, demon_name: str, player_name: str = "your") -> str:
		return f"-# `> {race} {demon_name} has been registered to {player_name} compendium.`"

	@staticmethod
	def dupe_level_up(player_id: int, demon: DemonData, dupe_message: str):
		new_dupe_level = demon.dupes + 1
		level_string = "MAX" if new_dupe_level == 5 else str(new_dupe_level)
		return (
			f"### <@{player_id}> {demon.race} {demon.name} has leveled up to {level_string}{Emotes.GEM.value}!"
			f"\n{dupe_message}"
		)


class PartyMsg(GenericMsg):
	@staticmethod
	def confirm_release(demon_name: str) -> str:
		return f"Are you sure you want to release **{demon_name}** from your party?"

	@staticmethod
	def demon_released(demon_name: str) -> str:
		return (
			f"### Good-Bye...\n**{demon_name}** will have a happy life in a faraway forest."
			f"You may never see your **{demon_name}** again."
		)

	@staticmethod
	def increase_party_cost_not_enough(cost: int, mag: int) -> str:
		return f"The cost to increase party slots is **{cost} MAG**. You need **{cost - mag}** more **MAG**!"

	@staticmethod
	def confirm_increase_party(number: int, cost: int) -> str:
		return (
			f"Would you like to increase your available party slots by **{number}**?"
			f"\n\nCost: **{cost} MAG**"
			"\n-# Cost increases by **500 MAG** per slot."
		)

	@staticmethod
	def increased_party_success(party_cap: int, number: int) -> str:
		return f"Your available party slots increased from **{party_cap}** to **{party_cap + number}**!"

	@staticmethod
	def chosen_to_lead(demon_name: str) -> str:
		return f"You've chosen **{demon_name}** to lead your party!"

	@staticmethod
	def leader_stats(mag_mult: float, gems: tuple, gem_progress: int, demon: DemonData) -> str:
		gem_text = " & ".join(gems).title()
		gem_progress = round(gem_progress / 10)
		progress_bar = f"{Unicode.FILLED_CIRCLE.value} " * gem_progress + f"{Unicode.UNFILLED_CIRCLE.value} " * (
			10 - gem_progress
		)
		return (
			f"**{demon.race} {demon.name}** is currently leading your party."
			f"\n\n-# **Rank:** {demon.rank}"
			f"\n-# **Level:** {demon.dupes}{Emotes.GEM.value}"
			f"\n-# **MAG Mult:** +{mag_mult}x"
			f"\n-# **Hunting:** {gem_text}"
			f"\n-# **Progress:**\n{progress_bar}"
		)


class CompendiumMsg(GenericMsg):
	@staticmethod
	def confirm_summon_cost(demon_name: str, cost: int) -> str:
		return f"Summoning a **{demon_name}** will cost **{cost} MAG**. Do you wish to continue?"

	@staticmethod
	def summon_cost_not_enough(demon_name: str, mag: int, cost: int) -> str:
		return f"Summoning a **{demon_name}** will cost **{cost} MAG**. You need **{cost - mag}** more **MAG**!"

	@staticmethod
	def summoned_to_party(race: str, name: str) -> str:
		return f"You have summoned **{race} {name}** to your party!"


class EncountersMsg(GenericMsg):
	@staticmethod
	def encounter_cooldown(time_until: tuple[int, ...]) -> str:
		h, m, s = time_until
		return f"Encounter is on cooldown. Try again in **{h}h**, **{m}m** and **{s}s**."

	@staticmethod
	def introduction(player_name: str) -> str:
		return (
			f"-# `> {player_name} has been registered to the DDS-Net! Enjoy your stay!`"
			"\n\nOnce you're done with your first `>encounter`, you can try another straight away!"
			" Explore the `>party` and `>comp` commands next."
			"\n\nYour first encounter will begin now..."
		)

	@staticmethod
	def get_status_message(
		existing_reg_status: DemonRegistration,
		demon: DemonData,
		user_name: str,
		mag_received: int,
		gems_added: int,
		gem_name: str,
	) -> str:
		match existing_reg_status:
			# Brand new demon.
			case DemonRegistration.UNREGISTERED:
				status = f"> {demon.race} {demon.name} was registered to {user_name}'s compendium! +{mag_received} MAG"

			# Demon will join the party but has already been registered before.
			case DemonRegistration.IN_COMP:
				status = f"> {demon.race} {demon.name} has joined {user_name}'s party! +{mag_received} MAG"

			# Demon already in the party.
			case DemonRegistration.IN_PARTY | DemonRegistration.ON_LOAN:
				status_addition = f"| +{DEFAULT_DEMON_MULT_INCREMENT}x Mult" if demon.dupes >= 5 else ""

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

	@staticmethod
	def get_dupe_message(new_dupe_level: int, race: str, name: str, mag_bonus: float | None) -> str | None:
		match DupeReward(new_dupe_level):
			case DupeReward.COLOUR:
				return (
					f"You have unlocked the ability to customise the side colour for your **{name}** (see `>demon_colour`)!"
				)

			case DupeReward.MAG_MULT:
				return (
					f"**{name}** has received a +{DEFAULT_DEMON_MULT_INCREMENT}x to its **MAG Multiplier**!"
					f" Any MAG received from this demon in future encounters will now be multiplied by **{mag_bonus}**!"
				)

			case DupeReward.RACE_MULT:
				return (
					f"**{name}** has contributed +{DEFAULT_RACE_MULT_INCREMENT}x to **{race}'s MAG Multiplier**!"
					f" Any MAG received from the **{race}** race will now be multiplied by **{mag_bonus}**!"
				)

			case DupeReward.GREETING:
				return f"You have unlocked the ability to customise the greeting for your **{name}** (see `>set_greeting`)!"

			case DupeReward.GRIMOIRE:
				return f"**{name}** has gifted you a special item: **Grimoire**!"

			case DupeReward.BADGE:
				return (
					f"You are now fully linked with **{name}**!"
					" A universal badge has been added to your player (see `>badges`)!"
					f"\n\n-# Any levels after this will add **+0.05x MAG multiplier** when interacting with **{name}**."
				)

			case _:
				return None


class CustomisationMsg(GenericMsg):
	@staticmethod
	def custom_option_locked(option: str, demon_name: str) -> str:
		return f"You do not have the ability to customise the {option} for **{demon_name}** yet."

	@staticmethod
	def custom_colour_updated(demon_name: str, colour: int) -> str:
		updated_string = f"updated to **#{colour:06X}**" if colour != 0 else "reverted to its **DEFAULT**"
		return f"**{demon_name}**'s embed colour has been {updated_string}."

	@staticmethod
	def custom_greeting_reverted(demon_name: str) -> str:
		return f"**{demon_name}**'s greeting has been reverted to its **DEFAULT**."

	@staticmethod
	def custom_greeting_not_valid(greeting_length: int) -> str:
		return f"Either your greeting is over {greeting_length} characters in length, or you're trying to be cheeky."

	@staticmethod
	def custom_greeting_updated(demon: DemonData, greeting: str) -> str:
		formatted_greeting = format_utils.format_greeting(greeting, demon)
		return f'**{demon.name}**\'s greeting has been updated to "{formatted_greeting}".'


class FusionMsg(GenericMsg):
	@staticmethod
	def already_in_fusion() -> str:
		return "You're already in the process of fusing..."

	@staticmethod
	def cant_fuse(demons: list[DemonData]) -> str:
		d1, d2 = demons
		return f"**{d1.race} {d1.name}** + **{d2.race} {d2.name}** = **Nothing!** So sorry about that champ!"

	@staticmethod
	def fusion_response(demons: list[DemonData], demon_result: DemonData) -> str:
		d1, d2 = demons
		return (
			f"**{d1.race} {d1.name}** ({d1.rank})"
			f" + **{d2.race} {d2.name}** ({d2.rank}) ="
			f"\n### {demon_result.race} {demon_result.name} ({demon_result.rank})"
			f"\n{Emotes.BLANK.value}"
			"\n"
		)

	@staticmethod
	def fusion_too_weak(strongest: int, leeway: int) -> str:
		return (
			"But you are too weak to control it..."
			f"\n\n-# You can control up to {strongest + leeway}"
			f" (Your strongest demon's rank + {leeway})."
		)

	@staticmethod
	def fusion_already_in_party(demon_result: DemonData) -> str:
		return (
			f"-# __**NOTE**__: **{demon_result.race} {demon_result.name}** can already be found in your party,"
			f" summoning it again will raise its level by 1{Emotes.GEM.value} instead."
		)

	@staticmethod
	def fusion_cost(cost: int) -> str:
		return f"Fusing these demons will cost **{cost} MAG**."

	@staticmethod
	def fusion_not_enough_mag(cost: int, mag: int) -> str:
		cost_string = FusionMsg.fusion_cost(cost)
		return f"{cost_string} You need **{cost - mag}** more **MAG**!"

	@staticmethod
	def confirm_fusion(cost: int) -> str:
		cost_string = FusionMsg.fusion_cost(cost)
		return f"{cost_string} Do you wish to continue?"

	@staticmethod
	def fusion_completed(race: str, demon_name: str, is_accident: bool = False, new_to_comp: bool = False) -> str:
		unexpected = "Hmm... It seems an unexpected demon was born... " if is_accident else ""
		registered = FusionMsg.registered_to_compendium(race, demon_name) if new_to_comp else ""

		return (
			f"{unexpected}"
			f"\n\n-# **{demon_name.upper()}**:"
			f"\n-# I'm **{race} {demon_name}**. Well, it's nice to meet you."
			f"\n\n{registered}"
		)

	@staticmethod
	def confirm_special_fusion(race: str, name: str, ingredients: tuple[IngredientData, ...]) -> str:
		ingredient_text = "".join(f"\n-# - {i.race} {i.name}" for i in ingredients)
		return (
			f"In order to summon **{race} {name}**, the following must be sacrificed:"
			f"{ingredient_text}"
			f"\n\nComplete the ritual?"
			"\n\n"
		)


class ItemMsg(GenericMsg):
	@staticmethod
	def item_doesnt_exist(item: str) -> str:
		return f"The item, **{item}**, doesn't exist."

	@staticmethod
	def not_in_inventory(item: str) -> str:
		return f"You do not have enough **{item}**."

	@staticmethod
	def currently_on_loan(demon_name: str) -> str:
		return f"**{demon_name}** is currently being loaned to the Server Compendium and can't use items..."

	@staticmethod
	def exclusive_to_fail(demon_name: str, item: str) -> str:
		return f"**{demon_name}** is not a part of the race that can use **{item}**."

	@staticmethod
	def confirm_use_item(qty_owned: int, item: str, number_to_use: int, demon_name: str) -> str:
		return (
			f"You own **{qty_owned} {item}(s)**. Are you sure you want to use **{number_to_use}** on your **{demon_name}**?"
		)

	@staticmethod
	def use_item_completed(player_id: int, item: str, demon_name: str, increment: int) -> str:
		return f"<@{player_id}> has used **{item}** on **{demon_name}**! Their rank has **increased** by **{increment}**."

	@staticmethod
	def empty_inventory() -> str:
		return "Your inventory is empty."

	@staticmethod
	def found_gem(player_id, name: str, gem: str) -> str:
		return f"<@{player_id}>, your **{name}** has found a **{gem.title()}**!"


class ProfileMsg(GenericMsg):
	@staticmethod
	def no_badges() -> str:
		return "You have no badges."

	@staticmethod
	def show_badges(badges: list[BadgeData]) -> str:
		show_badges = ""
		for b in badges:
			show_badges += f"<:{b.name}:{b.emote_id}>"
		return show_badges


class ServerCompendiumMsg(GenericMsg):
	@staticmethod
	def already_loaning(name: str) -> str:
		return f"You are already loaning **{name}**."

	@staticmethod
	def confirm_loan(race: str, name: str, stored_rank: int, server_name: str) -> str:
		return (
			f"Do you wish to loan your **{race} {name}** (Rank **{stored_rank}**)"
			f" to **{server_name}'s Compendium**?\n\n"
			f"-# You will not be able to use the demon again until they are retrieved."
		)

	@staticmethod
	def someone_has_loaned(stored_owner: str, name: str, stored_rank: int, server_name: str) -> str:
		return f"**{stored_owner}**'s **{name}** (Rank {stored_rank}) is already in {server_name}'s Compendium."

	@staticmethod
	def confirm_replace_loaned(stored_owner: str, name: str, server_name: str, player_rank: int, owner_rank: int) -> str:
		return (
			f"**{stored_owner}** is already loaning their **{name}** to **{server_name}'s Compendium**."
			f"\nYour {name} is stronger ({player_rank} to {owner_rank})."
			"\n-# Do you wish to replace it? The demon will be returned to its owner."
			f"\n\n-# You will not be able to use the demon again until they are retrieved."
		)

	@staticmethod
	def returned_to_owner(owner_name: str, demon_name: str) -> str:
		return f"\n\n>`{owner_name}'s {demon_name} has been returned to its owner's COMP`"

	@staticmethod
	def loan_completed(race: str, name: str, stored_rank: int, server_name: str) -> str:
		return (
			f"Your **{race} {name}** (Rank {stored_rank})"
			f" has been sacrificed to **{server_name}'s Compendium** for the time being."
		)

	@staticmethod
	def not_found_on_loan(name: str) -> str:
		return f"**{name}** was not found on loan..."

	@staticmethod
	def confirm_return(race: str, name: str, stored_rank: int, server_name: str) -> str:
		return (
			f"Are you sure you want to retrieve **{race} {name}** (Rank {stored_rank}) from **{server_name}'s Compendium**?"
		)

	@staticmethod
	def return_completed(race: str, name: str) -> str:
		return f"**{race} {name}** has been returned to you."

	@staticmethod
	def level_change_notif(rewards: set[str], server_name: str, old_level: int, new_level: int, stats: ServerStats) -> str:
		if old_level < new_level:
			message_string = f"{server_name.upper()} LEVELED UP FROM LEVEL **{old_level}** TO **{new_level}**!"
		else:
			rewards = ServerCompendiumMsg.adjust_level_desc(rewards)
			message_string = f"{server_name.upper()} LEVELED DOWN FROM LEVEL **{old_level}** TO **{new_level}**..."

		reward_list = ""
		for r in rewards:
			reward_list += f"\n-# - {r}"

		stats_string = (
			f"\nExperience required to next level: **{stats.xp_required}**"
			f"\nTotal Server Experience: **{stats.total_xp}**"
			f"\nEncounters can now appear up to Rank: **{stats.rank_cap}**"
		)

		return f"### {message_string}{stats_string}\n\n-# **New Rewards:**{reward_list}"

	@staticmethod
	def adjust_level_desc(level_desc: set[str]) -> set[str]:
		"""Returning set means we will not double up on rewards. Won't just be a bunch of "Rank Cap Increased"'s"""
		adjusted = set()

		# Adjust descriptions in-place: replace 'Increased' with 'Decreased' in values
		for d in level_desc:
			if "Increased" in d:
				d = d.replace("Increased", "Decreased")
			elif "Unlocked" in d:
				d = d.replace("Unlocked", "Locked")
			adjusted.add(d)

		return set(adjusted)

	@staticmethod
	def show_server_stats(server_name: str, stats: ServerStats) -> str:
		progress_xp = int((stats.current_level_xp / stats.xp_required) * 10)
		progress_bar = f"{Unicode.FILLED_CIRCLE.value} " * progress_xp + f"{Unicode.UNFILLED_CIRCLE.value} " * (
			10 - progress_xp
		)

		return (
			f"### {server_name}'s Server Statistics"
			f"\n\nServer Level: **{stats.level}**"
			f"\n\nMaximum Encounter Rank: **{stats.rank_cap}**"
			f"\n\nTotal Experience: **{stats.total_xp}**"
			f"\n\nExperience to Next Level: **{stats.current_level_xp}** / **{stats.xp_required}**"
			f"\n{progress_bar}"
		)


class ShopMsgs(GenericMsg):
	@staticmethod
	def not_enough_gems(item_name: str) -> str:
		return f"You don't have enough gems to purchase **{item_name}**."

	@staticmethod
	def purchase_success(item_name: str) -> str:
		return f"You have purchased a **{item_name}**!"

	@staticmethod
	def rags_dialogue() -> str:
		options = [
			"Mmmm... You smell strongly of gems. Welcome. I'll trade anything with you.",
			"Anything I got, it's yours. For a small fee, of course.",
			"Put your MAG away, I only believe in gemstones. What would you like?",
		]

		return f"-# **RAG:**\n-# {choice(options)}"

	@staticmethod
	def rags_info() -> str:
		return (
			"-# - Trade gemstones for incense that can be used to increase the rank of one of your demons."
			"\n-# - Each demon requires an incense for their respective race."
			# "\n-# - As the demon grows in strength, larger incense will be required. (NOT YET IMPLEMENTED)"
		)

	@staticmethod
	def build_item_title(item_name: str, cost: dict[str, int]) -> str:
		gem_amounts = []
		for gem, amount in cost.items():
			gem_amounts.append(f"{gem.title()} x{amount}")
		return f"**{item_name}** - {', '.join(gem_amounts)}"

	@staticmethod
	def build_item_desc(desc: str) -> str:
		return f"-# {desc}"

	@staticmethod
	def mido_dialogue() -> str:
		options = [
			"Welcome to the Cathedral of Shadows, where demons gather...",
		]

		return f"-# **MIDO:**\n-# {choice(options)}"

	@staticmethod
	def special_fusion_info() -> str:
		return (
			"-# - Perform a Special Fusion by sacrificing the necessary demons from your party."
			"\n-# - Special Fusion Keys can be found by leveling up the server and through events."
		)

	@staticmethod
	def build_sp_fusion_title(race: str, name: str, rank: int) -> str:
		return f"**{race} {name}** (Rank {rank})"

	@staticmethod
	def build_sp_fusion_required(ingredients: tuple[IngredientData, ...]) -> str:
		ingredient_list = []

		for i in ingredients:
			ingredient_list.append(f"{i.race} {i.name}")

		return f"-# **Required:** {' + '.join(ingredient_list)}"


class UtilityMsgs(GenericMsg):
	@staticmethod
	def build_stuff_details(mag: int, encounter_string: str, daily_string: str, stats_string: str) -> str:
		return f"MAG: **{mag}**\n\n{encounter_string}\n\n{daily_string}\n\n{stats_string}"

	@staticmethod
	def get_daily_available(time_until: tuple[int, ...] | None) -> str:
		if time_until is None:
			return "Daily is available!"
		h, m, s = time_until
		return f"Daily available in **{h}h**, **{m}m** and **{s}s**."

	@staticmethod
	def get_encounter_available(time_until: tuple[int, ...] | None) -> str:
		if time_until is None:
			return "Encounter is available!"
		h, m, s = time_until
		return f"Encounter available in **{h}h**, **{m}m** and **{s}s**."

	@staticmethod
	def get_encounter_stats(rank_cap: int, average_rank: int, strongest_rank: int, leeway: int):
		return (
			f"- Encounters can spawn up to **Rank {rank_cap}** (Server Cap)."
			f"\n- Encounters are weighted to **Rank {average_rank}** (Your Party Average)."
			f"\n- Encounters under **Rank {strongest_rank + leeway}** can be recruited"
			f" (Your Strongest Demon + {leeway})."
		)

	@staticmethod
	def discovered_mag(mag: int, total_mag: int) -> str:
		return f"You've discovered a cluster of **{mag}** MAG! Your total is now **{total_mag}** MAG."

	@staticmethod
	def show_dedicated_channel(channel_id: int) -> str:
		return (
			f"Encounters are only appearing in <#{channel_id}>."
			" You can update this by using `>set_channel {channel_name}`."
		)

	@staticmethod
	def set_dedicated_channel(channel_id: int) -> str:
		return f"Encounters will now only appear in <#{channel_id}>"
