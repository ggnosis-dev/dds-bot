from discord.ext import commands
from helpers.players import Players


class IsDeveloperCheck(commands.CheckFailure):
	'''Exception for specific developer.'''
	pass

class NotInServerCheck(commands.CheckFailure):
	'''Custom exception for failed in-server check.'''
	pass


class ProfileSetupCheck(commands.CheckFailure):
	'''Custom exception for failed profile setup check.'''
	pass


def is_developer():
	def predicate(ctx: commands.Context):
		return ctx.author.id == 233142721819312128
	return commands.check(predicate)


def is_admin():
	return commands.check_any(
		commands.is_owner(),
		commands.has_permissions(administrator = True)
	)


def in_server():
	def predicate(ctx: commands.Context):
		if ctx.guild is None:
			raise NotInServerCheck("Now how exactly did the bot get here?")
		
		return True
	
	return commands.check(predicate)


def has_profile():
	async def predicate(ctx: commands.Context):
		if ctx.guild is None:
			raise RuntimeError("ERROR: Server ID could not be determined.")

		player_db = Players()
		has_profile = player_db.check_player_exists(ctx.author.id, ctx.guild.id)
		if not has_profile:
			raise ProfileSetupCheck("You don't have a profile set up yet! Use `>start` to begin.")
		
		return True
	
	return commands.check(predicate)