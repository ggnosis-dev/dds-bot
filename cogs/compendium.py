import typing

import discord

from discord.ext import commands

from helpers import checks, currency_queries, demon_queries, player_queries
from helpers.views import Columns, CompendiumView, ConfirmationView, MessageView
from shared_enums import DemonRegistration


class Compendium(commands.Cog):
	"""Cog for viewing and summoning from player compendiums."""

	def __init__(self, bot: commands.Bot) -> None:
		"""Init the Compendium cog with reference to bot instance and database classes."""
		self.bot = bot
		self.demon_db = demon_queries.DemonQueries()
		self.player_db = player_queries.PlayerQueries()

	@commands.command(name="compendium", aliases=["comp", "c"], help="Displays the player's compendium.")
	async def compendium_command(self, ctx: commands.Context, mentioned: discord.Member | None = None) -> None:
		"""
		Command to display player's seen demons which is stored in their compendium.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check compendium for.
		"""
		guild = typing.cast(discord.Guild, ctx.guild)
		player = mentioned if mentioned is not None else ctx.author

		comp_list = await self.player_db.check_compendium(player.id, guild.id)
		view = CompendiumView(player.name, comp_list, Columns.PLAYER_DEFAULT)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(name="summon", aliases=["sum"], help="Summon a demon from the player's compendium.")
	async def summon_command(self, ctx, *, demon_name) -> None:
		"""
		Command to summon a demon from the player's compendium into their party.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to summon. The * before it in the arguments
				allows for multi-word demon names.
		"""
		guild = typing.cast(discord.Guild, ctx.guild)
		player = ctx.author
		demon_name = demon_name.title()
		demon_id = self.demon_db.get_demon_id_by_name(demon_name)
		cost = 200

		if demon_id is None:
			msg = MessageView(f"The demon **{demon_name}** was not found in your compendium.")
			await ctx.send(view=msg)
			return

		# Check if demon is in compendium before summoning to give a more informative message.
		in_comp = await self.player_db.check_demon_registration(player.id, guild.id, demon_id)

		if in_comp == DemonRegistration.UNREGISTERED:
			msg = MessageView(f"The demon **{demon_name}** was not found in your compendium.")
			await ctx.send(view=msg)
			return

		if in_comp == DemonRegistration.IN_PARTY:
			msg = MessageView(f"You already have **{demon_name}** in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view with the cost.
		view = ConfirmationView(f"Summoning a **{demon_name}** will cost **{cost} MAG**. Do you wish to continue?")
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		# Check if player has enough mag to summon. Comes after confirmation view as player's may want to just see cost.
		mag = currency_queries.get_mag(player.id, guild.id)

		if mag < cost:
			msg = MessageView("You don't have enough Magnetite to summon this demon!")
			await ctx.send(view=msg)
			return

		currency_queries.update_mag(player.id, guild.id, -cost)
		await self.player_db.set_demon_in_party(player.id, guild.id, demon_id, True)
		msg = MessageView(f"You have summoned **{demon_name}** to your party!")
		await ctx.send(view=msg)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Compendium(bot))
