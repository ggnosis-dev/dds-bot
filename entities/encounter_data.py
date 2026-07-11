from dataclasses import dataclass

from shared_enums import Personality, ResponseType


@dataclass
class ReactionData:
	personality: Personality
	responseType: ResponseType
	response: str


@dataclass
class AnswerData:
	label: str
	reactions: list[ReactionData]


@dataclass
class TalkData:
	question: str
	answers: tuple[AnswerData, ...]
