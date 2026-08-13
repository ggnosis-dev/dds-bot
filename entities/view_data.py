from dataclasses import dataclass

import discord

from shared_enums import Emotes


@dataclass
class ColumnConfig:
	# Key should match the database column's name.
	key: str
	label: str
	width: int = 0
	header_tabs: int = 1
	align: str = "^"


@dataclass
class Columns:
	# Comp Exclusive.
	REGISTRY = ColumnConfig(key="in_party", label=Emotes.BLANK.value)
	RACE = ColumnConfig(key="race", label="Race", width=12, header_tabs=3)
	NAME = ColumnConfig(key="name", label="Name", width=18, header_tabs=6)
	EXP = ColumnConfig(key="initial_rank", label="Exp", width=3, header_tabs=2, align=">")
	STORED_RANK = ColumnConfig(key="stored_rank", label="Rank", width=3, header_tabs=4, align=">")
	OWNER = ColumnConfig(key="owner", label="Owner", width=12, header_tabs=3)
	GEMS = ColumnConfig(key="gems", label="Gemstone", width=12, header_tabs=3)
	TONE = ColumnConfig(key="tone_name", label="Tone", width=12, header_tabs=3)

	PLAYER_DEFAULT = [REGISTRY, RACE, NAME, STORED_RANK]
	COMP_DEFAULT = PLAYER_DEFAULT
	SERVER_DEFAULT = COMP_DEFAULT + [EXP, OWNER]

	# Item/Gem Collection Exclusive.
	EMOTE = ColumnConfig(key="emote", label=Emotes.BLANK.value)
	ITEM_NAME = ColumnConfig(key="name", label="Name", width=12, header_tabs=3)
	QUANTITY = ColumnConfig(key="quantity", label="Quantity", width=3, header_tabs=3, align=">")

	ITEM_DEFAULT = [EMOTE, ITEM_NAME, QUANTITY]


def get_args(args: tuple[str, ...], server: discord.Guild, column_layout: list):
	mentioned = None
	sorted_args = sorted(args)

	for arg in sorted_args:
		arg = arg.lower()

		# arg is a mention like <@111122223333>, extract numeric id.
		if arg.startswith("<@") and arg.endswith(">"):
			digits = "".join(ch for ch in arg if ch.isdigit())
			mentioned = server.get_member(int(digits)) if digits else None

		elif "experience".startswith(arg):
			if Columns.EXP not in column_layout:
				column_layout.append(Columns.EXP)

		elif "gemstones".startswith(arg):
			if Columns.GEMS not in column_layout:
				column_layout.append(Columns.GEMS)

		elif "tone".startswith(arg):
			if Columns.TONE not in column_layout:
				column_layout.append(Columns.TONE)

	return column_layout, mentioned
