from dataclasses import dataclass

from shared_enums import Personality, ResponseType


@dataclass
class ReactionData:
	personality: Personality
	responseType: ResponseType
	response: str


@dataclass
class TalkData:
	question: str
	answers: dict[str, list[ReactionData]]
