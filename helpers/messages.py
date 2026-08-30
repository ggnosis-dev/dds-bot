class CompendiumMsg:
	@staticmethod
	def not_in_comp(demon_name: str) -> str:
		return f"The demon **{demon_name}** was not found in your compendium."

	@staticmethod
	def party_full() -> str:
		return "Your party is full! You can increase capacity using `>increase_party`."

	@staticmethod
	def already_in_party() -> str:
		return "You already have this demon in your party..."

	@staticmethod
	def summon_cost(demon_name: str, cost: int) -> str:
		return f"Summoning a **{demon_name}** will cost **{cost} MAG**. Do you wish to continue?"

	@staticmethod
	def summon_cost_not_enough(demon_name: str, mag: int, cost: int) -> str:
		return f"Summoning a **{demon_name}** will cost **{cost} MAG**. You need **{cost - mag}** more **MAG**."

	@staticmethod
	def summoned_to_party(race: str, name: str) -> str:
		return f"You have summoned **{race} {name}** to your party!"


class EncountersMsg:
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
