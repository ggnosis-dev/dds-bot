from dataclasses import dataclass


@dataclass
class CommandData:
	name: str
	help: str
	usage: str
	aliases: list[str] | None = None
	hidden: bool = False
	require_var_positional: bool = False


def command_kwargs(command_type: dict[str, CommandData], key: str):
	data = command_type[key]
	return {
		"name": data.name,
		"aliases": data.aliases,
		"help": data.help,
		"usage": data.usage,
		"hidden": data.hidden,
	}


COMPENDIUM_COMMANDS = {
	"compendium": CommandData(
		name="compendium",
		aliases=["comp", "c"],
		help=(
			"View your Demonic Compendium, letting you see every demon you have ever recruited."
			" You can view other player's Compendiums by tagging them,"
			' and can view hidden columns by typing part of "gemstone" or "personality".'
		),
		usage=">compendium {opt: @player | gemstone | personality}",
	),
	"summon": CommandData(
		name="summon",
		aliases=["sum"],
		help=(
			"Summon a registered demon from your Demonic Compendium to your Party for a fee."
			" Provide the demon's name after the command."
		),
		usage=">summon | >sum {demon}",
		require_var_positional=True,
	),
}

DEMONS_COMMANDS = {
	"select": CommandData(
		name="select",
		aliases=["sel"],
		help="Select a demon to lead your Party. The selected demon will hunt for gemstones while you use the server.",
		usage=">select | >sel {demon}",
	),
	"leader": CommandData(
		name="leader",
		aliases=["le"],
		help="View the status of the demon leading your Party.",
		usage=">leader | >le",
	),
}

ENCOUNTERS_COMMANDS = {
	"encounter": CommandData(
		name="encounter",
		aliases=["e"],
		help=(
			"Starts an encounter with a demon."
			" Its rank is determined at random using distribution up to the Server's Maximum Rank Capacity "
			" with weight at your Party's Average Rank."
		),
		usage=">encounter | >e",
	),
	# TODO: Make deprecated.
	"start": CommandData(
		name="start",
		help="Sets up the player to start playing with the DDS-BOT.",
		usage=">start",
	),
	"test_encounter": CommandData(
		name="test_encounter",
		aliases=["te"],
		help="Developer Only. Start a test encounter with a random demon.",
		usage=">test_encounter | te {opt: demon}",
		hidden=True,
	),
}
