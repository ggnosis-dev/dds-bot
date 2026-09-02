import asyncio

from discord.ext import commands

from entities.command_data import SERVER_COMPENDIUM_COMMANDS, command_kwargs
from entities.view_data import Columns, get_args
from helpers import checks, gets
from helpers.messages import ServerCompendiumMsg as Messages
from queries import demon_queries, player_demons_queries, server_demons_queries, server_level_queries
from shared_enums import DemonRegistration
from views.common_view import ConfirmationView, MessageView
from views.table_view import ServerCompendiumView


class ServerCompendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "server_compendium"))
	async def server_compendium_command(self, ctx: commands.Context, *args: str) -> None:
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
	async def loan_command(self, ctx: commands.Context, *, demon_name: str | None) -> None:

		if demon_name is None:
			await MessageView.send(ctx.channel, Messages.no_input_given(SERVER_COMPENDIUM_COMMANDS["loan"]))
			return

		player_id, server_id = gets.get_player_server_ids(ctx)
		server_name = gets.get_server_name(ctx)
		demon_name = demon_name.title()
		demon_id = await demon_queries.get_demon_id_by_name(demon_name)

		if demon_id is None:
			await MessageView.send(ctx.channel, Messages.not_in_party(demon_name))
			return

		# Check if demon is summoned.
		player_demon, reg_status = await asyncio.gather(
			player_demons_queries.get_player_demon_by_id(player_id, server_id, demon_id),
			player_demons_queries.check_demon_registration(player_id, server_id, demon_id),
		)

		if reg_status == DemonRegistration.ON_LOAN:
			await MessageView.send(ctx.channel, Messages.already_loaning(demon_name))
			return

		# Do not let player's loan their leaders.
		if reg_status == DemonRegistration.LEADER:
			await MessageView.send(ctx.channel, Messages.currently_leader(demon_name))
			return

		if player_demon is None or reg_status != DemonRegistration.IN_PARTY:
			await MessageView.send(ctx.channel, Messages.not_in_party(demon_name))
			return

		# Get potential stored demon.
		stored_demon = await server_demons_queries.get_serv_comp_demon(server_id, player_demon.demon_id)
		returned_to_owner_msg = ""

		if stored_demon:
			# Check and prompt replace demon if possible.
			stored_owner = await self.bot.fetch_user(stored_demon.player_id)
			design_data = await demon_queries.get_design_data(demon_id, stored_demon.player_id, server_id)

			# If weaker, send message about it and return.
			if player_demon.stored_rank <= stored_demon.stored_rank:
				await MessageView.send(
					ctx.channel,
					Messages.someone_has_loaned(stored_owner.name, demon_name, stored_demon.stored_rank, server_name),
					thumbnail=design_data.profile_img,
					colour=design_data.colour,
				)
				return

			# Player demon is stronger, prompt to replace.
			message = Messages.confirm_replace_loaned(
				stored_owner.name, player_demon.name, server_name, player_demon.stored_rank, stored_demon.stored_rank
			)
			confirmed = await ConfirmationView.send(
				ctx.channel,
				message,
				player_id,
				confirm_label="Yes",
				deny_label="No",
				thumbnail=design_data.profile_img,
				colour=design_data.colour,
			)
			if not confirmed:
				return

			returned_to_owner_msg = Messages.returned_to_owner(stored_owner.name, demon_name)

		else:
			# Store a brand new demon.
			design_data = await demon_queries.get_design_data(demon_id, player_id, server_id)
			confirmed = await ConfirmationView.send(
				ctx.channel,
				Messages.confirm_loan(player_demon.race, player_demon.name, player_demon.stored_rank, server_name),
				exclusive_to=player_id,
				confirm_label="Yes",
				deny_label="No",
				thumbnail=design_data.profile_img,
				colour=design_data.colour,
			)
			if not confirmed:
				return

		# Both types of checks have passed, add to the server compendium.
		await server_demons_queries.new_add_demon_to_server_compendium(player_id, server_id, player_demon.demon_id)

		# Send final message first, append returned to owner message if exists.
		message = Messages.loan_completed(player_demon.race, player_demon.name, player_demon.stored_rank, server_name)
		message += returned_to_owner_msg
		await MessageView.send(ctx.channel, message, thumbnail=design_data.profile_img, colour=design_data.colour)

		# If a stored_demon existed, then we need to take and add back EXP.
		add_exp = player_demon.stored_rank
		if stored_demon:
			add_exp = player_demon.stored_rank - stored_demon.stored_rank
		await self._do_level_change(ctx, server_id, server_name, add_exp)

	@checks.has_profile()
	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "return"))
	async def return_command(self, ctx: commands.Context, *, demon_name: str | None) -> None:

		if demon_name is None:
			await MessageView.send(ctx.channel, Messages.no_input_given(SERVER_COMPENDIUM_COMMANDS["loan"]))
			return

		player_id, server_id = gets.get_player_server_ids(ctx)
		server_name = gets.get_server_name(ctx)
		demon_name = demon_name.title()
		demon = await demon_queries.get_demon_by_name(player_id, server_id, demon_name)

		if demon is None:
			await MessageView.send(ctx.channel, Messages.not_found_on_loan(demon_name))
			return

		# Get the stored demon, return if it's not owned or found.
		stored_demon = await server_demons_queries.get_serv_comp_demon(server_id, demon.id)
		print(stored_demon)
		if stored_demon is None or player_id != stored_demon.player_id:
			await MessageView.send(ctx.channel, Messages.not_found_on_loan(demon_name))
			return

		# Confirm return.
		confirmed = await ConfirmationView.send(
			ctx.channel,
			Messages.confirm_return(demon.race, demon.name, stored_demon.stored_rank, server_name),
			exclusive_to=player_id,
			confirm_label="Yes",
			deny_label="No",
			colour=demon.design_data.colour,
		)
		if not confirmed:
			return

		# Return the player's demon.
		await server_demons_queries.return_server_comp_demon(server_id, demon.id)

		# Remove the experience from the server's level.
		remove_exp = -stored_demon.stored_rank

		# Remove and send final message.
		await asyncio.gather(
			MessageView.send(
				ctx.channel,
				Messages.return_completed(demon.race, demon.name),
				thumbnail=demon.design_data.profile_img,
				colour=demon.design_data.colour,
			),
			self._do_level_change(ctx, server_id, server_name, remove_exp),
		)

	@commands.command(**command_kwargs(SERVER_COMPENDIUM_COMMANDS, "server_stats"))
	async def server_stats_command(self, ctx: commands.Context) -> None:
		server = gets.get_server(ctx)
		image = server.icon.url if server.icon is not None else None
		stats = await server_level_queries.get_server_status(server.id)
		await MessageView.send(ctx.channel, Messages.show_server_stats(server.name, stats), thumbnail=image)

	async def _do_level_change(self, ctx: commands.Context, server_id: int, server_name: str, exp_change: int) -> None:
		level_data, stats = await asyncio.gather(
			server_level_queries.try_server_level_up(server_id, exp_change),
			server_level_queries.get_server_status(server_id),
		)

		if level_data.old_level != level_data.new_level:
			# Get all the reward descriptions.
			reward_descs = {reward.desc for reward in level_data.rewards}

			await MessageView.send(
				ctx.channel,
				Messages.level_change_notif(
					reward_descs,
					server_name,
					level_data.old_level,
					level_data.new_level,
					stats,
				),
			)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(ServerCompendium(bot))
