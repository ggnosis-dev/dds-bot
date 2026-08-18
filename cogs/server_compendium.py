import asyncio
import typing

from collections import Counter

import discord

from discord.ext import commands

from entities.command_data import SERVER_COMPENDIUM_COMMANDS, command_kwargs
from entities.view_data import Columns, get_args
from helpers import checks, gets
from queries import demon_queries, player_demons_queries, server_demons_queries, server_level_queries
from shared_enums import DemonRegistration, Unicode
from views.common_view import ConfirmationView, MessageView
from views.table_view import ServerCompendiumView


class ServerCompendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		"""Init the Compendium cog with reference to bot instance and database classes."""
		self.bot = bot

	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "server_compendium"))
	async def server_comp_command(self, ctx: commands.Context, *args: str) -> None:
		try:
			server = gets.get_server(ctx)

			columns = list(Columns.SERVER_DEFAULT)
			columns, mentioned = get_args(args, server, columns) if args else (columns, None)
			mentioned = mentioned.id if mentioned else None
			need_gems = Columns.GEMS in columns

			comp_list, stats = await asyncio.gather(
				server_demons_queries.check_server_compendium(server.id, mentioned, need_gems),
				server_level_queries.get_server_status(server.id),
			)

			# Because the server COMP only stores user IDs, we need to retrieve their names through a cache lookup.
			for entry in comp_list:
				if entry.owner_id is not None:
					player = server.get_member(entry.owner_id)
					entry.owner_name = player.display_name if player else "Unknown"

			view = ServerCompendiumView(server.name, comp_list, columns, server_stats=stats)
			await ctx.send(view=view)
		except Exception as e:
			print(f"server_compendium.py | server_comp_command | {e}")

	@checks.has_profile()
	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "loan"))
	async def loan_command(self, ctx: commands.Context, *, demon_name: str) -> None:

		player, server = gets.get_player_server(ctx)
		demon_name = demon_name.title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)

		if demon_id is None:
			msg = MessageView(f"**{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Do not let player's loan their leaders.
		selected_d_id = await player_demons_queries.get_selected_demon_id(player.id, server.id)
		if demon_id == selected_d_id:
			msg = MessageView(f"**{demon_name}** cannot be loaned as they are currently leading your party...")
			await ctx.send(view=msg)
			return

		# Check if demon is in party.
		player_demon, in_party, design_data = await asyncio.gather(
			player_demons_queries.get_player_demon_by_id(player.id, server.id, demon_id),
			player_demons_queries.check_demon_registration(player.id, server.id, demon_id),
			demon_queries.get_design_data(demon_id),
		)

		if player_demon is None or in_party != DemonRegistration.IN_PARTY:
			msg = MessageView(f"**{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(
			f"Do you wish to loan your **{player_demon.race} {player_demon.name}** (Rank **{player_demon.stored_rank}**)"
			f" to **{server.name}'s Compendium**?\n\n"
			f"-# You will not be able to use the demon again until they are retrieved.",
			exclusive_to=player.id,
			confirm_label="Yes",
			deny_label="No",
			thumbnail=design_data.profile_url,
			colour=design_data.colour,
		)
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		success = await server_demons_queries.add_demon_to_server_compendium(player.id, server.id, player_demon.demon_id)

		# If a demon is already stored, check if they can overwrite it.
		if success is False:
			stored_demon = await server_demons_queries.get_single_serv_comp_demon(server.id, player_demon.demon_id)
			stored_owner = typing.cast(discord.Member, self.bot.get_user(stored_demon.player_id))

			# If weaker, send message regarding that.
			if player_demon.stored_rank <= stored_demon.stored_rank:
				msg = MessageView(
					f"**{stored_owner}**'s **{demon_name}** (Rank {stored_demon.stored_rank}) "
					f"is already in {server.name}'s Compendium.",
					thumbnail=design_data.profile_url,
					colour=design_data.colour,
				)
				await ctx.send(view=msg)
				return

			# If stronger, prompt to overwrite.
			view = ConfirmationView(
				f"**{stored_owner}** is already loaning their **{player_demon.name}** to **{server.name}'s Compendium**."
				f"\nYour {player_demon.name} is stronger ({player_demon.stored_rank} to {stored_demon.stored_rank})."
				"\n-# Do you wish to replace it? The demon will be returned to its owner."
				f"\n\n-# You will not be able to use the demon again until they are retrieved.",
				exclusive_to=player.id,
				confirm_label="Replace",
				deny_label="Cancel",
				thumbnail=design_data.profile_url,
				colour=design_data.colour,
			)
			result = await ConfirmationView.send_message(view, ctx)

			if result is False or result is None:
				return

			await server_demons_queries.replace_server_compendium_demon(
				player.id,
				server.id,
				player_demon.demon_id,
			)

			# Add experience to the server's level. Take away stored demon first, then add new.
			r1, r2 = await asyncio.gather(
				server_level_queries.try_server_level_up(server.id, -stored_demon.stored_rank),
				server_level_queries.try_server_level_up(server.id, player_demon.stored_rank),
			)

			if r1 or r2:
				# Start level is either the first old level or the second old level.
				old_level = r1.old_level if r1 else r2.old_level

				# New level is either the furthest new level or the first new level.
				new_level = r2.new_level if r2 else r1.new_level

				change = new_level - old_level

				reward_descs = set()

				# Gained a level.
				if change > 0:
					# If we gained, the rewards will only ever be in results 2.
					reward_descs = {reward.desc for reward in r2.rewards}
				elif change < 0:
					# Rewards in r1 will be subtracted.
					lost_rewards = r1.rewards

					# Chance there were rewards regained though, e.g. went down a level yet still gained 2.
					regained_rewards = r2.rewards

					lost_count = Counter(lost_rewards)
					regained_count = Counter(regained_rewards)

					gained = list((regained_count - lost_count).elements())
					lost = list((lost_count - regained_count).elements())

					# Pull out the descriptions of lost and alter them.
					gained_descs = {reward.desc for reward in gained}
					lost_descs = self._adjust_level_up_desc({reward.desc for reward in lost})
					reward_descs = lost_descs | gained_descs

				await self._do_level_up_notif(ctx, server, old_level, new_level, reward_descs)

			msg = MessageView(
				f"Your **{player_demon.race} {player_demon.name}** (Rank {player_demon.stored_rank})"
				f" has been sacrificed to **{server.name}'s Compendium** for the time being."
				f"\n\n>`{stored_owner.mention}'s {player_demon.name} has been returned to its owner's COMP`",
				thumbnail=design_data.profile_url,
				colour=design_data.colour,
			)
			await ctx.send(view=msg)
			return

		msg = MessageView(
			f"Your **{player_demon.race} {player_demon.name}** (Rank {player_demon.stored_rank})"
			f" has been sacrificed to **{server.name}'s Compendium** for the time being.",
			thumbnail=design_data.profile_url,
			colour=design_data.colour,
		)
		await ctx.send(view=msg)

		# Add experience to the server's level.
		level_data = await server_level_queries.try_server_level_up(server.id, player_demon.stored_rank)
		if level_data.old_level != level_data.new_level:
			reward_descs = {reward.desc for reward in level_data.rewards}
			await self._do_level_up_notif(ctx, server, level_data.old_level, level_data.new_level, reward_descs)

	@checks.has_profile()
	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "return"))
	async def return_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		player, server = gets.get_player_server(ctx)
		demon_name = demon_name.title()
		demon = demon_queries.get_demon_by_name(demon_name)

		if demon is None:
			msg = MessageView(f"**{demon_name}** was not found on loan...")
			await ctx.send(view=msg)
			return

		stored_demon = await server_demons_queries.get_single_serv_comp_demon(server.id, demon.id)

		if stored_demon is not None and player.id == stored_demon.player_id:
			view = ConfirmationView(
				f"Are you sure you want to retrieve **{demon.race} {demon.name}** (Rank {stored_demon.stored_rank}) "
				f"from **{server.name}'s Compendium**?",
				exclusive_to=player.id,
				confirm_label="Yes",
				deny_label="No",
				colour=demon.design_data.colour,
			)
			result = await ConfirmationView.send_message(view, ctx)

			if result is False or result is None:
				return

			if await server_demons_queries.return_server_comp_demon(server.id, demon.id):
				# Remove the experience from the server's level.

				msg = MessageView(
					f"**{demon.race} {demon.name}** has been returned to you.",
					demon.design_data.profile_url,
					demon.design_data.colour,
				)
				await ctx.send(view=msg)

				level_data = await server_level_queries.try_server_level_up(server.id, -stored_demon.stored_rank)

				if level_data.old_level != level_data.new_level:
					reward_descs = self._adjust_level_up_desc({reward.desc for reward in level_data.rewards})
					await self._do_level_up_notif(ctx, server, level_data.old_level, level_data.new_level, reward_descs)

	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "server_stats"))
	async def server_stats_command(self, ctx: commands.Context) -> None:
		server = gets.get_server(ctx)
		stats = await server_level_queries.get_server_status(server.id)
		image = server.icon.url if server.icon is not None else None

		progress_xp = int((stats.current_level_xp / stats.xp_required) * 10)

		progress_bar = f"{Unicode.FILLED_CIRCLE.value} " * progress_xp + f"{Unicode.UNFILLED_CIRCLE.value} " * (
			10 - progress_xp
		)

		msg = MessageView(
			f"### {server.name}'s Server Statistics"
			f"\n\nServer Level: **{stats.level}**"
			f"\n\nMaximum Encounter Rank: **{stats.rank_cap}**"
			f"\n\nTotal Experience: **{stats.total_xp}**"
			f"\n\nExperience to Next Level: **{stats.current_level_xp}** / **{stats.xp_required}**"
			f"\n{progress_bar}",
			thumbnail=image,
		)
		await ctx.send(view=msg)

	async def _do_level_up_notif(
		self, ctx: commands.Context, server: discord.Guild, old_level: int, new_level: int, rewards: set[str]
	) -> None:
		reward_list = ""
		serv_stats = await server_level_queries.get_server_status(server.id)
		for r in rewards:
			reward_list += f"\n-# - {r}"

		if old_level < new_level:
			message_string = f"{server.name.upper()} LEVELED UP FROM LEVEL **{old_level}** TO **{new_level}**!"
		else:
			message_string = f"{server.name.upper()} LEVELED DOWN FROM LEVEL **{old_level}** TO **{new_level}**..."

		stats = (
			f"\nExperience required to next level: **{serv_stats.xp_required}**"
			f"\nTotal Server Experience: **{serv_stats.total_xp}**"
			f"\nEncounters can now appear up to Rank: **{serv_stats.rank_cap}**"
		)

		msg = MessageView(f"### {message_string}{stats}\n\n-# **New Rewards:**{reward_list}")
		await ctx.send(view=msg)

	def _adjust_level_up_desc(self, level_desc: set[str]) -> set[str]:
		"""Returning set means we will not double up on rewards. Won't just be a bunch of "Rank Cap Increased"'s"""
		adjusted = set()

		# Adjust descriptions in-place: replace 'Increased' with 'Decreased' in values
		for d in level_desc:
			if "Increased" in d:
				d = d.replace("Increased", "Decreased")
			elif "Unlocked" in d:
				d = d.replace("Unlocked", "Locked")
			adjusted.add(d)

		return set(adjusted)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(ServerCompendium(bot))
