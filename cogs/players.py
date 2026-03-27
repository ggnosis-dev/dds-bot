import discord
from discord.ext import commands
from enum import Enum
import csv


class PlayerData:
	def __init__(self, id: int, server_id: int, party: list[str], compendium: list[str]):
		self.id = id
		self.server_id = server_id
		self.party = party
		self.compendium = compendium

	def save_to_csv(self, file_path: str):
		with open(file_path, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([self.id, self.server_id, [], []])

class Players(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def setup_player(self, ctx):
		id = ctx.author.id
		server_id = ctx.guild.id
		playerData = PlayerData(id, server_id, [], [])
		
		await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")

		playerData.save_to_csv("players.csv")
		
		await ctx.send("Your profile has been set up! You can now start playing.")


async def setup(bot):
	await bot.add_cog(Players(bot))
