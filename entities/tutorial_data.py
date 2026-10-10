from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial

from discord.ext import commands

from queries import currency_queries, gem_queries


@dataclass
class TutorialTask:
	name: str
	hint: str
	check: TaskCheck


@dataclass
class TutorialStep:
	# Is a bitmask. 000 = 0, 011 = 3 (task 1 and 2 completed), 101 = 5 (tasks 1 and 3), etc.
	desc_step: str
	desc_tasks: dict[int, TutorialTask]
	reward_text: str
	# on_complete will be an awaitable callable with any amount of args (...).
	on_complete: Callable[..., Awaitable[object]]


@dataclass
class TutorialEvent:
	# "command" or "trigger"
	kind: str
	name: str
	args: tuple[str, ...] | None = None


# Get command context and return bool if task completed.
TaskCheck = Callable[[TutorialEvent], Awaitable[bool]]


def get_command_args(ctx: commands.Context) -> tuple[str, ...]:
	assert ctx.command is not None

	# Find the ctx index first so we can start directly after it.
	ctx_index = ctx.args.index(ctx)
	args = ctx.args[ctx_index + 1 :]

	# Return lowercase.
	return tuple(str(arg).lower() for arg in args)


def ran_command(name: str) -> TaskCheck:
	async def check(event: TutorialEvent) -> bool:
		return event.kind == "command" and event.name == name

	return check


def ran_command_with_argument(name: str, params: tuple[str, ...], ordered: bool = False) -> TaskCheck:
	async def check(event: TutorialEvent) -> bool:
		if event.kind != "command" or event.name != name or event.args is None:
			return False

		if ordered:
			# This should evaluate to True if in the right order.
			return event.args == params

		# Sort both lists so they are now in the same order.
		return sorted(event.args) == sorted(params)

	return check


def ran_trigger(name: str) -> TaskCheck:
	async def check(event: TutorialEvent) -> bool:
		return event.kind == "trigger" and event.name == name

	return check


async def gem_reward(player_id, server_id, gem_dict):
	for name, qty in gem_dict.items():
		await gem_queries.add_gem(player_id, server_id, gems=(name,), number=qty)


TUTORIAL_STEPS = {
	1: TutorialStep(
		desc_step="Welcome to the DDS-Net!",
		desc_tasks={
			1: TutorialTask(
				name="Fairy Pixie Appears!",
				hint="Use `>encounter` to witness your first demon.",
				check=ran_command("encounter"),
			),
			2: TutorialTask(
				name="Joining the DDS-Net",
				hint="Use `>tutorial` to see... Well, this helpful page!",
				check=ran_command("tutorial"),
			),
			3: TutorialTask(
				name="Hee-Huh?",
				hint="Use `>help` to see a helpful list of commands.",
				check=ran_command("help"),
			),
		},
		reward_text="500 MAG",
		# Partial takes function and prefills args that will now only need the remaining update_mag args.
		# 500 MAG is enough to do >increase_party.
		on_complete=partial(currency_queries.update_mag, amount=500),
	),
	2: TutorialStep(
		desc_step="Registration Complete! Teaching Fundamentals",
		desc_tasks={
			1: TutorialTask(
				name='Think This Legally has to be Called "Party Time"',
				hint="Use `>party` to see the demons you've collected so far.",
				check=ran_command("party"),
			),
			2: TutorialTask(
				name="Compendium",
				hint=(
					"Use `>compendium gems` to see every demon you've registered and the usually hidden gem column"
					" (these can be used with similar views like `>party` and there are more hidden columns available)."
				),
				check=ran_command_with_argument("compendium", ("gems",)),
			),
			3: TutorialTask(
				name="View Entry",
				hint="Use `>entry` to view details about your registered demons.",
				check=ran_command("entry"),
			),
			4: TutorialTask(
				name="Increase Party Slots",
				hint="Use `>increase_party` to increase the number of party slots you have.",
				check=ran_trigger("increase_party"),
			),
			# 5: TutorialTask(
			# 	name="I'm Putting Together a Team",
			# 	hint="Register 5 demons to your Compendium.",
			# 	check=ran_command("help"),
			# ),
		},
		reward_text="Amethyst x2, Agate x1",
		on_complete=partial(gem_reward, gem_dict={"AMETHYST": 2, "AGATE": 1}),
	),
	3: TutorialStep(
		desc_step="Gemstones",
		desc_tasks={
			1: TutorialTask(
				name="Check Gems",
				hint="Use `>gems` to see your gem collection.",
				check=ran_command("gems"),
			),
			2: TutorialTask(
				name="Fairy Incense",
				hint="Use `>rags` to visit Rag's Jewelry and purchase a Fairy Incense.",
				check=ran_trigger("rags_fairy"),
			),
			3: TutorialTask(
				name="Use the Incense",
				hint="Use `>use Fairy Incense; <name>` to use a useful incense on a useful Fairy.",
				check=ran_trigger("used_fairy_incense"),
			),
			4: TutorialTask(
				name="Leader",
				hint="Use `>leader` to change who hunts for gemstones.",
				check=ran_trigger("leader_set"),
			),
			5: TutorialTask(
				name="Find a Gem",
				hint="Have an encounter gift you a gem.",
				check=ran_trigger("encounter_gem"),
			),
		},
		reward_text="500 MAG",
		on_complete=partial(currency_queries.update_mag, amount=500),
	),
	4: TutorialStep(
		desc_step="End",
		desc_tasks={
			1: TutorialTask(
				name="I'm Just Being Lazy and not protecting against key overflow",
				hint="No really, I should just do that...",
				check=ran_command("give_mag"),
			),
		},
		reward_text="End of Tutorial",
		on_complete=partial(currency_queries.update_mag, amount=500),
	),
}
