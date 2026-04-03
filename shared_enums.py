from enum import Enum

class Emotes(Enum):
	ONE = '\u0031\ufe0f\u20e3'
	TWO = '\u0032\ufe0f\u20e3'
	THREE = '\u0033\ufe0f\u20e3'
	ICON = '<:__:1486233309078884493>'
	BLANK = '<:__:1486236397508628510>'

class Personality(Enum): 
	CHEERFUL = 1
	SHY = 2
	AGGRESSIVE = 3

class DemonRegistration(Enum):
	IN_PARTY = 1
	IN_COMP = 2
	UNREGISTERED = 3

class ResponseType(Enum):
	GOOD = 1
	NEUTRAL = 2
	BAD = 3