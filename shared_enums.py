from enum import Enum


class Emotes(Enum):
	ONE = "\u0031\ufe0f\u20e3"
	TWO = "\u0032\ufe0f\u20e3"
	THREE = "\u0033\ufe0f\u20e3"
	ICON = "<:ic:1526860349700182188>"
	LOAN = "<:ic_loan:1526860351432560650>"
	LEAD = "<:ic_lead:1526860641195786251>"
	HUH = "<:ic_huh:1529383425650458694>"
	BLANK = "<:__:1524640707732570183>"
	GEM = "<:gm:1524641174458073159>"
	GEM_THIN = "<:gt:1524641170011979806>"
	KNOT = "<:kn:1524641172356730880>"


class Unicode(Enum):
	FILLED_CIRCLE = "\u2b24"
	UNFILLED_CIRCLE = "\u25ef"


class Personality(Enum):
	NONE = 0
	CHEERFUL = 1
	CALM = 2
	AGGRESSIVE = 3


class DemonRegistration(Enum):
	IN_PARTY = 0
	IN_COMP = 1
	UNREGISTERED = 2
	CANT_JOIN = 3


class ResponseType(Enum):
	GOOD = 1
	NEUTRAL = 2
	BAD = 3


class Gem(Enum):
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


class Banners(Enum):
	RAGS = "https://cdn.discordapp.com/attachments/1521163871732371688/1521330221297565817/rag_w_title.png?ex=6a4470ad&is=6a431f2d&hm=e450b99d56eb5168cb494896fa8bc65ed609cf5241a2e6fcc6b4c9dda6199ae5&"
	SP_FUSION = "https://cdn.discordapp.com/attachments/1521163871732371688/1521367712503435415/special_w_text.png?ex=6a449398&is=6a434218&hm=3065c982ca7f67afe5d50791be41e036b09c55a6603ce83072ff22e8fa8d8208&"


class ShopColour(Enum):
	RAGS = 0x1B6340
	SP_FUSION = 0x0000A7


class Tone(Enum):
	NONE = 0
	JACK = 1
	CUTE = 2
	ROOKIE = 3
	BRUTE = 4
	FATALE = 5
	PEPPY = 6
	MONSTER = 7
	POMPOUS = 8
	OLD = 9
	BEAST = 10
	WISE = 11
	DIVINE = 12
