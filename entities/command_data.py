from dataclasses import dataclass


@dataclass
class CommandData:
	name: str
	help: str
	usage: str
	aliases: list[str] | None = None
	hidden: bool = False


def command_kwargs(command_type: dict[str, CommandData], key: str):
	data = command_type[key]
	return_data = {
		"name": data.name,
		"help": data.help,
		"usage": data.usage,
		"hidden": data.hidden,
	}

	if data.aliases is not None:
		return_data["aliases"] = data.aliases

	return return_data


COMPENDIUM_COMMANDS = {
	"compendium": CommandData(
		name="compendium",
		aliases=["comp", "c"],
		help=(
			"View your Demonic Compendium, letting you see every demon you have ever recruited."
			" You can view other player's Compendiums by mentioning them,"
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
			" Its rank is determined at random using distribution up to the Server's Maximum Rank Capacity"
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

FUSION_COMMANDS = {
	"fuse": CommandData(
		name="fuse",
		aliases=["f"],
		help=(
			"Fuse two demons together into another demon."
			" Fusing with a demon from the Element race will create a demon that is a"
			" tier up or down in the other demon's race."
			"\nSupposedly accidents can occur..."
		),
		usage=">fuse | f {demon_1}; {demon_2}",
	)
}

GEMS_COMMANDS = {
	"gems": CommandData(
		name="gems",
		aliases=["g"],
		help="Displays your current Gem Collection.",
		usage=">gems | g",
	)
}

ITEMS_COMMANDS = {
	"inventory": CommandData(
		name="inventory",
		aliases=["inv"],
		help="View your inventory of acquired items.",
		usage=">inventory | inv",
	),
	"use": CommandData(
		name="use",
		help=(
			"Use an item on a demon."
			" If no demon is specified, the item will be used on the current demon leading your party."
		),
		usage=">use {item}; {opt: demon}",
	),
}

PARTY_COMMANDS = {
	"party": CommandData(
		name="party",
		aliases=["p"],
		help=(
			"Displays the player's current Party."
			" You can view other player's Compendiums by mentioning them,"
			' and can view hidden columns by typing part of "gemstone" or "personality".'
		),
		usage=">party | p {opt: @player | gemstone | personality}",
	),
	"increase_party": CommandData(
		name="increase",
		aliases=["inc"],
		help=(
			"Increase number of slots available in your party."
			" Multiple can be upgraded at once by specifying a number."
			" Each new slot's cost increments by 500 MAG."
		),
		usage=">increase | inc {opt: number}",
	),
	"release": CommandData(
		name="release",
		aliases=["rel"],
		help=(
			"Release a demon from your Party to free up space."
			" This does not remove it from your Compendium and you can resummon them anytime using the `>summon` command."
			"\nOccassionally, the demon may give you something as a parting gift."
		),
		usage=">release | rel {demon}",
	),
}
