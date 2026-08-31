from entities.command_data import CommandData
from entities.demon_data import DEFAULT_DEMON_MULT_INCREMENT, DEFAULT_RACE_MULT_INCREMENT, DemonData
from helpers import format_utils
from shared_enums import DemonRegistration, DupeReward, Emotes, Unicode


class GenericMsg:
	@staticmethod
	def not_in_party(demon_name: str) -> str:
		return f"**{demon_name}** was not found in your party..."

	@staticmethod
	def not_in_comp(demon_name: str) -> str:
		return f"The demon **{demon_name}** was not found in your compendium."

	@staticmethod
	def currently_on_loan(demon_name: str) -> str:
		return f"**{demon_name}** is currently being loaned to the Server Compendium..."

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
		return f"{command.help}\n\n-# `{command.usage}`"


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
	def encounter_cooldown(hours: int, minutes: int, seconds: int) -> str:
		return f"Encounter is on cooldown. Try again in **{hours}h**, **{minutes}m** and **{seconds}s**."

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
