from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial

from discord.ext import commands

from queries import currency_queries

# Get command context and return bool if task completed.
TaskCheck = Callable[[commands.Context], Awaitable[bool]]


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


def ran_command(name: str) -> TaskCheck:
	async def check(ctx: commands.Context) -> bool:
		assert ctx.command is not None, "Run command check should only occur in on_command_completion."
		return ctx.command.name == name

	return check


TUTORIAL_STEPS = {
	1: TutorialStep(
		desc_step="Learn the fundamentals",
		desc_tasks={
			1: TutorialTask(
				name="Fairy Pixie Appears!",
				hint="Use `>encounter` to witness your first demon.",
				check=ran_command("encounter"),
			),
			2: TutorialTask(
				name="Discovering the DDS-Net",
				hint="Use `>tutorial` to see... Well, this helpful page!",
				check=ran_command("tutorial"),
			),
			3: TutorialTask(
				name='Think this legally has to be Called "Party Time"',
				hint="Use `>party` to see the demons you've collected so far.",
				check=ran_command("party"),
			),
		},
		reward_text="500 MAG",
		# Partial takes function and prefills args that will now only need the remaining update_mag args.
		on_complete=partial(currency_queries.update_mag, amount=500),
	)
}
