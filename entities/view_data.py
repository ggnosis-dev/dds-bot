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
	RANK = ColumnConfig(key="rank", label="Rank", width=3, header_tabs=4, align=">")
	OWNER = ColumnConfig(key="owner", label="Owner", width=12, header_tabs=3)
	GEM = ColumnConfig(key="gem", label="Gemstone", width=12, header_tabs=3)
	PERSONALITY = ColumnConfig(key="personality", label="Personality", width=12, header_tabs=3)

	PLAYER_DEFAULT = [REGISTRY, RACE, NAME, RANK]
	SERVER_DEFAULT = PLAYER_DEFAULT + [OWNER]

	# Item/Gem Collection Exclusive.
	EMOTE = ColumnConfig(key="emote", label=Emotes.BLANK.value)
	ITEM_NAME = ColumnConfig(key="name", label="Name", width=12, header_tabs=3)
	QUANTITY = ColumnConfig(key="quantity", label="Quantity", width=3, header_tabs=3, align=">")

	ITEM_DEFAULT = [EMOTE, ITEM_NAME, QUANTITY]


def get_args(args: tuple[str, ...], server: discord.Guild, column_layout: list):
	mentioned = None

	for arg in args:
		arg = arg.lower()

		# arg is a mention like <@111122223333>, extract numeric id.
		if arg.startswith("<@") and arg.endswith(">"):
			digits = "".join(ch for ch in arg if ch.isdigit())
			mentioned = server.get_member(int(digits)) if digits else None

		elif "gemstone".startswith(arg):
			if Columns.GEM not in column_layout:
				column_layout.append(Columns.GEM)

		elif "personality".startswith(arg):
			if Columns.PERSONALITY not in column_layout:
				column_layout.append(Columns.PERSONALITY)

	return column_layout, mentioned
