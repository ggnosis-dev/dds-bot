import asyncio

from discord.ext import commands

from entities.command_data import DEMONS_COMMANDS, command_kwargs
from entities.demon_data import GREETING_LENGTH
from helpers import checks, format_utils, gets, utils
from helpers.messages import CustomisationMsg
from queries import demon_queries, player_demons_queries
from shared_enums import DemonRegistration
from views.common_view import MessageView


class CustomisationCommands(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "demon_colour"))
	async def demon_colour_command(self, ctx: commands.Context, *, input_str: str | None) -> None:

		if input_str is None:
			await MessageView.send(ctx.channel, CustomisationMsg.no_input_given(DEMONS_COMMANDS["demon_colour"]))
			return

		player_id, server_id = gets.get_player_server_ids(ctx)
		parts = input_str.split(";")
		demon_name = parts[0].strip().title()
		demon_id = await demon_queries.get_demon_id_by_name(demon_name)

		reg_status = (
			await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
			if demon_id is not None
			else DemonRegistration.UNREGISTERED
		)

		# Check if demon is valid. If it is, still check registration as to not reveal demons player haven't seen yet.
		if demon_id is None or reg_status == DemonRegistration.UNREGISTERED:
			await MessageView.send(ctx.channel, CustomisationMsg.not_in_comp(demon_name))
			return

		# Anything that returns implies the player has access to customising.
		old_colour = await player_demons_queries.get_custom_colour_on_demon(player_id, server_id, demon_id)
		if old_colour is None:
			await MessageView.send(ctx.channel, CustomisationMsg.custom_option_locked("embed colour", demon_name))
			return

		# Set to 0 (returns to DEFAULT) if no second part was provided.
		hex_string = parts[1].strip() if len(parts) > 1 else None
		new_colour = utils.get_hex_colour(hex_string) if hex_string else 0

		# Update colour and send complete message.
		await asyncio.gather(
			player_demons_queries.set_custom_colour_on_demon(player_id, server_id, demon_id, new_colour),
			MessageView.send(ctx.channel, CustomisationMsg.custom_colour_updated(demon_name, new_colour), colour=new_colour),
		)

	@checks.has_profile()
	@commands.command(**command_kwargs(DEMONS_COMMANDS, "set_greeting"))
	async def set_greeting_command(self, ctx: commands.Context, *, input_str: str | None = None) -> None:

		if input_str is None:
			await MessageView.send(ctx.channel, CustomisationMsg.no_input_given(DEMONS_COMMANDS["set_greeting"]))
			return

		player_id, server_id = gets.get_player_server_ids(ctx)
		parts = input_str.split(";")
		demon_name = parts[0].strip().title()
		demon_id = await demon_queries.get_demon_id_by_name(demon_name)

		reg_status = (
			await player_demons_queries.check_demon_registration(player_id, server_id, demon_id)
			if demon_id is not None
			else DemonRegistration.UNREGISTERED
		)

		# Check if demon is valid. If it is, still check registration as to not reveal demons player haven't seen yet.
		if demon_id is None or reg_status == DemonRegistration.UNREGISTERED:
			await MessageView.send(ctx.channel, CustomisationMsg.not_in_comp(demon_name))
			return

		# Anything past here implies the player has access to customising.
		old_greeting = await player_demons_queries.get_custom_greeting_on_demon(player_id, server_id, demon_id)
		if old_greeting is None:
			await MessageView.send(ctx.channel, CustomisationMsg.custom_option_locked("greeting", demon_name))
			return

		# Want demon for design data and for greeting example after confirmation.
		demon = await demon_queries.get_demon_by_id(player_id, server_id, demon_id)
		greeting_string = parts[1].strip() if len(parts) > 1 else None

		# No greeting given, reset to default.
		if greeting_string is None:
			# Set greeting with default and send reverted message.
			await asyncio.gather(
				player_demons_queries.set_custom_greeting_on_demon(player_id, server_id, demon_id),
				MessageView.send(
					ctx.channel,
					CustomisationMsg.custom_greeting_reverted(demon_name),
					thumbnail=demon.design_data.profile_img,
					colour=demon.design_data.colour,
				),
			)
			return

		# [r]/[R] and [d]/[D] are required so other player's can still see what it is.
		if "[r]" not in greeting_string.lower() or "[d]" not in greeting_string.lower():
			await MessageView.send(ctx.channel, CustomisationMsg.no_input_given(DEMONS_COMMANDS["set_greeting"]))
			return

		# Sanitise the message to make sure it's under the character limit and doesn't have evil things in it.
		sanitised_greeting = format_utils.sanitise_input(greeting_string, GREETING_LENGTH)
		if sanitised_greeting is None:
			await MessageView.send(ctx.channel, CustomisationMsg.custom_greeting_not_valid(GREETING_LENGTH))
			return

		# Save the sanitised string.
		await asyncio.gather(
			player_demons_queries.set_custom_greeting_on_demon(player_id, server_id, demon_id, sanitised_greeting),
			MessageView.send(ctx.channel, CustomisationMsg.custom_greeting_updated(demon, sanitised_greeting)),
		)


class Demons(CustomisationCommands):
	def __init__(self, bot):
		self.bot = bot


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Demons(bot))
