from enum import Enum


class Emotes(Enum):
	ONE = "\u0031\ufe0f\u20e3"
	TWO = "\u0032\ufe0f\u20e3"
	THREE = "\u0033\ufe0f\u20e3"
	ICON = "<:__:1486233309078884493>"
	BLANK = "<:__:1486236397508628510>"


class Unicode(Enum):
	FILLED_CIRCLE = "\u2b24"
	UNFILLED_CIRCLE = "\u25ef"


class Personality(Enum):
	CHEERFUL = 1
	SHY = 2
	AGGRESSIVE = 3


class DemonRegistration(Enum):
	IN_PARTY = 1
	IN_COMP = 2
	UNREGISTERED = 3
	CANT_JOIN = 4


class ResponseType(Enum):
	GOOD = 1
	NEUTRAL = 2
	BAD = 3


class GemList(Enum):
	AGATE = 0
	AMETHYST = 1
	AQUAMARINE = 2
	CORAL = 3
	DIAMOND = 4
	EMERALD = 5
	GARNET = 6
	JADE = 7
	ONYX = 8
	OPAL = 9
	PEARL = 10
	RUBY = 11
	SAPPHIRE = 12
	TOPAZ = 13
	TURQUOISE = 14


class LevelRewardType(Enum):
	RANK = 0
	SP_FUSION_KEY = 1
	KEY = 2
	# MULT = 1
	# COOLDOWN = 2
