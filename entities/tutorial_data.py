from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial

from discord.ext import commands

from queries import currency_queries, gem_queries, player_demons_queries


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
	player_id: int
	server_id: int
	args: tuple[str, ...] | None = None


# Get command context and return bool if task completed.
TaskCheck = Callable[[TutorialEvent], Awaitable[bool]]
QueryCheck = Callable[[int, int], Awaitable[bool]]


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


def check_using_query(query: QueryCheck, allowed_commands: tuple[str, ...]) -> TaskCheck:
	async def check(event: TutorialEvent) -> bool:
		# Prevent spamming ourselves with checks every command.
		if event.name not in allowed_commands:
			return False

		return await query(event.player_id, event.server_id)

	return check


def party_average_check(target: int) -> QueryCheck:
	async def query(player_id: int, server_id: int) -> bool:
		stats = await player_demons_queries.get_party_stats(player_id, server_id)
		return stats.average >= target

	return query


def party_size_check(target: int) -> QueryCheck:
	async def query(player_id: int, server_id: int) -> bool:
		stats = await player_demons_queries.get_party_stats(player_id, server_id)
		return stats.size >= target

	return query


def gem_amount_check(target: int) -> QueryCheck:
	async def query(player_id: int, server_id: int) -> bool:
		gems = await gem_queries.get_player_gems(player_id, server_id)
		return len(gems) >= target

	return query


async def give_gem_reward(player_id, server_id, gem_dict):
	for name, qty in gem_dict.items():
		await gem_queries.add_gem(player_id, server_id, gems=(name,), number=qty)


###
# Steps:
# 1. Very Basics. Help, Encounter and Views.
# 2. Get some demons
# 3. Loaning and Server Compendium
# 4. Learn about Gems
#

# 			3: TutorialTask(
# 	name="Increase Party Slots",
# 	hint="Use `>increase_party` to increase the number of party slots you have.",
# 	check=ran_trigger("increase_party"),
# ),
# 5: TutorialTask(
# 	name="I'm Putting Together a Team",
# 	hint="Register 5 demons to your Compendium.",
# 	check=ran_command("help"),
# ),
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
				name='Think This Legally has to be Called "Party Time"',
				hint="Use `>party` to see the demons you've collected so far.",
				check=ran_command("party"),
			),
			3: TutorialTask(
				name="Compendium",
				hint=("Use `>compendium` to see every demon you've registered."),
				check=ran_command("compendium"),
			),
			4: TutorialTask(
				name="View Pixie's Entry",
				hint="Use `>entry Pixie` to view details about your registered demons.",
				check=ran_command_with_argument("entry", ("pixie",)),
			),
			5: TutorialTask(
				name="Daily MAG",
				hint="Use `>daily` to get some daily MAG. It is one of the main forms of currency.",
				check=ran_command("daily"),
			),
			6: TutorialTask(
				name="Hee-Huh?",
				hint="Use `>help` to see a helpful list of commands.",
				check=ran_command("help"),
			),
		},
		reward_text="100 MAG",
		# Partial takes function and prefills args that will now only need the remaining update_mag args.
		on_complete=partial(currency_queries.update_mag, amount=100),
	),
	2: TutorialStep(
		desc_step="Server Compendium",
		desc_tasks={
			1: TutorialTask(
				name="I'm Putting Together a Team",
				hint="Register 3 demons to your Compendium then run `>party`.",
				check=check_using_query(party_average_check(3), ("party",)),
			),
			2: TutorialTask(
				name="Loan Something to the Server Compendium",
				hint=(
					"Try to `>loan <name>` a demon to the Server's Compendium. Loaning will help raise the maximum rank"
					" (Server Cap) that encounters can spawn at for everyone."
				),
				check=ran_command("loan"),
			),
			3: TutorialTask(
				name="View Server Compendium",
				hint="Use `>server_compendium` to view every demon that is currently being loaned by players.",
				check=ran_command("server_compendium"),
			),
			4: TutorialTask(
				name="Raise Party Average to 5 then run stuff command",
				hint=(
					"Encounters are weighted to spawn demons at the Party's Average Rank."
					" Add demons to your party until your Party Average is 5 then run the `>stuff` command."
				),
				check=check_using_query(party_average_check(5), ("stuff",)),
			),
			5: TutorialTask(
				name="Server Stats",
				hint="Use `>server_stats` to view details about the server.",
				check=ran_command("server_stats"),
			),
		},
		reward_text="Amethyst x2, Agate x1",
		# Gems to get a Fairy Incense.
		on_complete=partial(give_gem_reward, gem_dict={"AMETHYST": 2, "AGATE": 1}),
	),
	3: TutorialStep(
		desc_step="Gemstones",
		desc_tasks={
			1: TutorialTask(
				name="Have 5 Unique Gems",
				hint="Have 5 unique gems in your collection, then run `>gems`.",
				check=check_using_query(gem_amount_check(5), ("gems",)),
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
		desc_step="Increasing Capabilities",
		desc_tasks={
			1: TutorialTask(
				name="I'm Putting Together a Team",
				hint="Register 10 demons to your Compendium then run `>party`.",
				check=check_using_query(party_average_check(10), ("party",)),
			),
			2: TutorialTask(
				name="Views with Extra Columns",
				hint=(
					"Use `>party tone` to see the usually hidden tone column.  These can be used with similar views like"
					" `>compendium` and there are other hidden columns available (see `>help`)."
				),
				check=ran_command_with_argument("party", ("tone",)),
			),
			3: TutorialTask(
				name="Increase Party Slots",
				hint="Use `>increase_party` to increase the number of party slots you have.",
				check=ran_trigger("increase_party"),
			),
		},
		reward_text="500 MAG",
		on_complete=partial(currency_queries.update_mag, amount=500),
	),
	5: TutorialStep(
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
