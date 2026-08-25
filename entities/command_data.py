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


COG_DESCRIPTIONS = {
	"Compendium": "Commands for viewing your registered demon collection",
	"Encounters": "Commands for encountering demons",
	"Fusion": "Commands to fuse two or more demons together",
	"Items": "Commands for the player's gems and item collections",
	"Party": "Commands for the demons currently in your party",
	"ServerCompendium": "Commands for viewing the server's registered demon collection",
	"Shop": "Commands for using the Rag's Jewelrey Shop",
	"Utility": "Commands for miscellaneous checks and tools",
}

COMPENDIUM_COMMANDS = {
	"compendium": CommandData(
		name="compendium",
		aliases=["comp", "c"],
		help=(
			"-# View your Demonic Compendium, letting you see every demon you have ever recruited."
			" You can view other player's Compendiums by mentioning them,"
			' and can view hidden columns by typing part of "experience", "gemstone" or "tone".'
		),
		usage=">compendium {opt: @player | experience | gemstone | tone}",
	),
	"summon": CommandData(
		name="summon",
		aliases=["sum"],
		help=(
			"-# Summon a registered demon from your Demonic Compendium to your Party for a fee."
			" Provide the demon's name after the command."
		),
		usage=">summon | sum {demon}",
	),
}

DEMONS_COMMANDS = {
	"demon_colour": CommandData(
		name="demon_colour",
		aliases=["demon_color", "dc"],
		help=(
			"-# If unlocked, change the embed colour for the specified demon."
			" Colour must be provided as a HEX colour code."
			" If no colour is provided, the demon will return to using its default colour."
		),
		usage=">demon_colour | demon_color | dc {demon}; {opt: hex_code}",
	),
	"select": CommandData(
		name="select",
		aliases=["sel"],
		help="-# Select a demon to lead your Party. The selected demon will hunt for gemstones while you use the server.",
		usage=">select | sel {demon}",
	),
	"leader": CommandData(
		name="leader",
		aliases=["le"],
		help="-# View the status of the demon leading your Party.",
		usage=">leader | le",
	),
}

ENCOUNTERS_COMMANDS = {
	"encounter": CommandData(
		name="encounter",
		aliases=["e"],
		help=(
			"-# Starts an encounter with a demon."
			"\n-# - Each demon has their own **Personality**, so tailor your response to make them happy."
			"\n-# - A demon won't join your party if the strongest demon in your party is significantly lower in rank to it."
			"\n-# - Demon's can appear in groups (up to 5 at a time), with more appearing as the playerbase grows."
			"\n-# - The demon's rank is determined using a random distribution;"
			" up to the **Server's Maximum Rank Capacity** (see **__Server Compendium__** for more details)"
			" and weighted at your own **Party's Average Rank**."
		),
		usage=">encounter | e",
	),
	"test_encounter": CommandData(
		name="test_encounter",
		aliases=["te"],
		help="-# **Developer Only.** Start a test encounter with a random demon.",
		usage=">test_encounter | te {opt: demon}",
	),
}

FUSION_COMMANDS = {
	"fuse": CommandData(
		name="fuse",
		aliases=["f"],
		help=(
			"-# Fuse two demons together into another demon."
			" Fusing with a demon from the Element race will create a demon that is a"
			" tier up or down in the other demon's race."
			"\n\n-# Supposedly accidents can occur..."
		),
		usage=">fuse | f {demon_1}; {demon_2}",
	),
	"special_fusion": CommandData(
		name="special_fusion",
		aliases=["sp_fuse", "sf"],
		help=(
			"-# Fuse more than two demons as ingredients in a special fusion for unique demons."
			" Certain special fusions can be found and unlocked through leveling up the server."
		),
		usage=">special_fusion | sp_fuse | sf",
	),
}

GEMS_COMMANDS = {
	"gems": CommandData(
		name="gems",
		aliases=["g"],
		help="-# Displays your current Gem Collection.",
		usage=">gems | g",
	)
}

ITEMS_COMMANDS = {
	"inventory": CommandData(
		name="inventory",
		aliases=["inv"],
		help="-# View your inventory of acquired items.",
		usage=">inventory | inv",
	),
	"use": CommandData(
		name="use",
		help=(
			"-# Use an item on a demon."
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
			"-# Displays the player's current Party."
			" You can view other player's Compendiums by mentioning them,"
			' and can view hidden columns by typing part of "experience", "gemstone" or "tone".'
		),
		usage=">party | p {opt: @player experience | gemstone | tone}",
	),
	"increase_party": CommandData(
		name="increase_party",
		aliases=["inp"],
		help=(
			"-# Increase number of slots available in your party."
			" Multiple can be upgraded at once by specifying a number."
			" Each new slot's cost increments by 500 MAG."
		),
		usage=">increase_party | inp {opt: number}",
	),
	"release": CommandData(
		name="release",
		aliases=["rel"],
		help=(
			"-# Release a demon from your Party to free up space."
			" This does not remove it from your Compendium and you can resummon them anytime using the `>summon` command."
		),
		usage=">release | rel {demon}",
	),
}

SERVER_COMPENDIUM_COMMANDS = {
	"loan": CommandData(
		name="loan",
		aliases=["ln"],
		help=(
			"-# Loan a demon to the Server's Demonic Compendium."
			"\n-# - The demon's rank will help contribute to the overall **Server Level**'s experience."
			"\n-# - A demon can be retrieved again at anytime using the `>return` command."
			"\n-# - If an existing demon is already in the Server's Compendium,"
			" a prompt to replace it will appear given your demon is stronger than it in personal rank."
		),
		usage=">loan | ln {demon}",
	),
	"return": CommandData(
		name="return",
		aliases=["ret"],
		help=(
			"-# Retrieve a demon that has been loaned to the Server's Demonic Compendium."
			" The demon's initial rank will be subtracted from the overall Server Level's experience."
		),
		usage=">return | ret {demon}",
	),
	"server_compendium": CommandData(
		name="server_compendium",
		aliases=["servcomp", "sc"],
		help=(
			"-# Displays the **Server's Demonic Compendium**, letting you see every demon the server's members have loaned"
			" (see `>loan` command)."
			"\n-# - You can view specific player's loaned demons by mentioning them."
		),
		usage=">server_compendium | servcomp | sc {opt: @player}",
	),
	"server_stats": CommandData(
		name="server_stats",
		aliases=["ss"],
		help=(
			"-# View statistics about the server."
			" This includes its **Server Level**, **Server's Maximum Rank Capacity**, **Server Experience**"
			" and how much is required for the next level."
		),
		usage=">server_stats | ss",
	),
}

SHOP_RAGS_COMMANDS = {
	"rags": CommandData(
		name="rags",
		aliases=["r"],
		help=(
			"-# Trade gemstones with Rag at Rag's Jewelry for valuable items"
			" such as incense which can be used to increase the rank of an owned demon."
		),
		usage=">rags | r",
	),
}

UTILITY_COMMANDS = {
	"daily": CommandData(
		name="daily",
		aliases=["d"],
		help="-# Get some free MAG every day.",
		usage=">daily | d",
	),
	"give_mag": CommandData(
		name="give_mag",
		aliases=["gm"],
		help="-# **Developer Only**. Give MAG to self.",
		usage=">give_mag | gm {number}",
	),
	"set_channel": CommandData(
		name="set_channel",
		help="-# Set the dedicated channel for encounters and alerts.",
		usage=">set_channel {channel_id}",
	),
	"stuff": CommandData(
		name="stuff",
		aliases=["st"],
		help="-# Check statistics and timers for the player.",
		usage=">stuff | st",
	),
}
