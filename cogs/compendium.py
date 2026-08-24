from discord.ext import commands

from entities.command_data import COMPENDIUM_COMMANDS, command_kwargs
from entities.view_data import Columns, get_args
from helpers import checks, costs, gets
from queries import currency_queries, demon_queries, player_demons_queries
from shared_enums import DemonRegistration
from views.common_view import ConfirmationView, MessageView
from views.table_view import CompendiumView


class Compendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		"""Init the Compendium cog with reference to bot instance and database classes."""
		self.bot = bot

	@commands.command(**command_kwargs(COMPENDIUM_COMMANDS, "compendium"))
	async def compendium_command(self, ctx: commands.Context, *args: str) -> None:
		"""
		Command to display player's seen demons which is stored in their compendium.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check compendium for.
		"""
		player, server = gets.get_player_server(ctx)
		columns = list(Columns.COMP_DEFAULT)
		mentioned = None

		if args:
			columns, mentioned = get_args(args, server, columns)

		player = mentioned if mentioned is not None else player

		need_gems = Columns.GEMS in columns

		comp_list = await player_demons_queries.check_compendium(player.id, server.id, need_gems)
		view = CompendiumView(player.name, comp_list, columns)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(**command_kwargs(COMPENDIUM_COMMANDS, "summon"))
	async def summon_command(self, ctx, *, demon_name) -> None:
		"""
		Command to summon a demon from the player's compendium into their party.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to summon. The * before it in the arguments
				allows for multi-word demon names.
		"""
		player_id, server_id = gets.get_player_server_ids(ctx)
		demon_name = demon_name.title()
		demon = demon_queries.get_demon_by_name(demon_name)

		if demon is None:
			msg = MessageView(f"The demon **{demon_name}** was not found in your compendium.")
			await ctx.send(view=msg)
			return

		# Check if party has space.
		if not player_demons_queries.get_party_has_space(player_id, server_id):
			msg = MessageView(
				f"Cannot summon **{demon_name}**. Party is full. You can increase capacity using `>increase_party`."
			)
			await ctx.send(view=msg)
			return

		cost = costs.summon_cost(demon.rank)

		# Check if demon is in compendium before summoning to give a more informative message.
		in_comp = await player_demons_queries.check_demon_registration(player_id, server_id, demon.id)

		if in_comp == DemonRegistration.UNREGISTERED:
			msg = MessageView(f"The demon **{demon_name}** was not found in your compendium.")
			await ctx.send(view=msg)
			return

		if in_comp == DemonRegistration.IN_PARTY or in_comp == DemonRegistration.ON_LOAN:
			msg = MessageView(f"You already have **{demon_name}** in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view with the cost.
		view = ConfirmationView(
			f"Summoning a **{demon_name}** will cost **{cost} MAG**. Do you wish to continue?",
			player_id,
		)
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		# Check if player has enough mag to summon. Comes after confirmation view as player's may want to just see cost.
		mag = currency_queries.get_mag(player_id, server_id)

		if mag < cost:
			msg = MessageView("You don't have enough Magnetite to summon this demon!")
			await ctx.send(view=msg)
			return

		currency_queries.update_mag(player_id, server_id, -cost)
		await player_demons_queries.set_demon_in_party(player_id, server_id, demon.id)
		msg = MessageView(
			f"You have summoned **{demon_name}** to your party!", demon.design_data.encounter_img, demon.design_data.colour
		)
		await ctx.send(view=msg)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Compendium(bot))
