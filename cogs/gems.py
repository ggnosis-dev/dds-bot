import discord

from discord.ext import commands
# from shared_enums import Emotes, GemList


class GemCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = 'gems', aliases = ['g'], description = "Displays the player's current gem collection.")
	async def gem_collection_command(self, ctx) -> None:
		pass


class GemCollectionView(discord.ui.View):
	pass


