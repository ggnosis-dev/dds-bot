from dataclasses import dataclass


@dataclass
class CommandData:
	name: str
	aliases: list[str]
	help: str


COMPENDIUM_COMMANDS = {
	"compendium": CommandData(
		name="compendium",
		aliases=["comp", "c"],
		help=(
			"View your Demonic Compendium, letting you see every demon you have ever recruited."
			" You can view other player's Compendiums by tagging them,"
			' and can view hidden columns by typing part of "gemstone" or "personality".'
			"\ne.g. `>compendium {@player | gemstone | personality}"
		),
	),
	"summon": CommandData(
		name="summon",
		aliases=["sum"],
		help=(
			"Summon a registered demon from your Demonic Compendium to your Party for a fee."
			" Provide the demon's name after the command."
			"\ne.g. `>summon {demon}`."
		),
	),
}


def command_kwargs(command_type: dict[str, CommandData], key: str):
	data = command_type[key]
	return {
		"name": data.name,
		"aliases": data.aliases,
		"help": data.help,
	}
