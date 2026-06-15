from dataclasses import dataclass

from shared_enums import Emotes


@dataclass
class ColumnConfig:
	# Key should match the database column's name.
	key: str
	label: str
	width: int = 0
	header_tabs: int = 1
	align: str = "^"


class Columns:
	EMOTE = ColumnConfig(key="in_party", label=Emotes.BLANK.value)
	RACE = ColumnConfig(key="race", label="Race", width=12, header_tabs=3)
	NAME = ColumnConfig(key="name", label="Name", width=18, header_tabs=5)
	RANK = ColumnConfig(key="rank", label="Rank", width=3, header_tabs=3, align=">")
	OWNER = ColumnConfig(key="owner", label="Owner", width=12, header_tabs=3)
	GEM = ColumnConfig(key="gem", label="Gemstone", width=12, header_tabs=3)
	PERSONALITY = ColumnConfig(key="personality", label="Personality", width=12, header_tabs=3)

	PLAYER_DEFAULT = [EMOTE, RACE, NAME, RANK]
	SERVER_DEFAULT = PLAYER_DEFAULT + [OWNER]
