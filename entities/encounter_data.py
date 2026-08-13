from dataclasses import dataclass

from shared_enums import DemonRegistration, Personality, ResponseType, Tone


@dataclass
class ReactionData:
	personality: Personality
	response_type: ResponseType
	response: str


@dataclass
class AnswerData:
	label: str
	reactions: list[ReactionData]


@dataclass
class TalkData:
	question: str
	answers: tuple[AnswerData, ...]


@dataclass
class JoinData:
	registration: DemonRegistration
	status_message: str
	extra_response: str | None


party_full_extra_responses = {
	Tone.BEAST: "GRRRRR... ME WANT JOIN BUT YOU NO ROOM! SMELL YOU LATER!",
	Tone.BRUTE: "Maaaan you ain't got no room for me! Good chat but I'm outta here.",
	Tone.CUTE: "So you're cool and all but also, like, you don't have room in your party for me, soooo? Ciaaaooo?",
	Tone.DIVINE: "Child, cleanse thy party of its filth and seek myself out again.",
	Tone.FATALE: "Oh -- so your current demons are more important than me, huh? Hmph.",
	Tone.JACK: "Ho... Looks like your part-hee is full! Usus-hee-ly I'd charge for that but I'm feeling generous today, ho!",
	Tone.MONSTER: "URGNHHH... pARtY fULL!!!!!!!!!!!!!!!!",
	Tone.OLD: "Woah, not so fast fella! There ain't n'more for me!",
	Tone.PEPPY: "When were you going to tell me your party wAS FULL ALREADY?! Don't call me!",
	Tone.POMPOUS: "...You cannot accomodate me? Just take this and remove yourself already.",
	Tone.ROOKIE: "Your party's WAY too fat for me! You can take this instead, I already have a matching one!",
	Tone.WISE: "Despite the worthwhile conversation, you have no room for me. Let us converse if we cross paths again.",
}
