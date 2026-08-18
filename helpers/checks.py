from discord.ext import commands

from helpers import gets
from queries import player_queries, server_queries


class IsDeveloperCheck(commands.CheckFailure):
	"""Exception for specific developer."""

	pass


class NotInServerCheck(commands.CheckFailure):
	"""Custom exception for failed in-server check."""

	pass


class ProfileSetupCheck(commands.CheckFailure):
	"""Custom exception for failed profile setup check."""

	pass


class NotInSetChannel(commands.CheckFailure):
	"""Custom exception for failed in set dedicated channel check."""

	pass


def is_developer():
	def predicate(ctx: commands.Context):
		return ctx.author.id == 233142721819312128

	return commands.check(predicate)


def is_admin():
	return commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))


def in_set_channel():
	async def predicate(ctx: commands.Context):
		s_id = gets.get_server(ctx).id
		set_channel_id = await server_queries.get_dedicated_channel(s_id)

		# When set channel ID is -1, we don't have a set channel.
		if set_channel_id != ctx.channel.id and set_channel_id is not None:
			raise NotInSetChannel(
				f"Command restricted to <#{set_channel_id}>. Get an admin to use `>set_channel` to allow it elsewhere."
			)

		return True

	return commands.check(predicate)


def has_profile():
	async def predicate(ctx: commands.Context):
		if ctx.guild is None:
			raise RuntimeError("ERROR: Server ID could not be determined.")

		has_profile = player_queries.check_player_exists(ctx.author.id, ctx.guild.id)
		if not has_profile:
			raise ProfileSetupCheck("You don't have a profile set up yet! Use `>encounter` to get you set up!")

		return True

	return commands.check(predicate)


def has_server_profile():
	async def predicate(ctx: commands.Context):
		if ctx.guild is None:
			raise RuntimeError("ERROR: Server ID could not be determined.")

		has_serv_profile = server_queries.check_server_exists(ctx.guild.id)

		if not has_serv_profile:
			server_queries.update_server_in_db(ctx.guild.id)

		return True

	return commands.check(predicate)
