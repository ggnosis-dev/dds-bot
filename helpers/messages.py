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
