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


class Players(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def setup_player(self, ctx) -> bool:
		print('GOT HERE')
		id = ctx.author.id
		server_id = ctx.guild.id
		player_data = PlayerData(id, server_id, [], [])

		if self.check_player_exists(player_data):
			await ctx.send("You already have a profile set up on this server!")
			return False
		
		await ctx.send(f"Welcome to the bot {ctx.author.mention}! Setting up your profile now...")

		self.save_to_csv(player_data)
		
		await ctx.send("Your profile has been set up! You can now start playing.")
		return True

	def save_to_csv(self, player: PlayerData):
		with open("players.csv", 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([player.id, player.server_id, player.party, player.compendium])


	def check_player_exists(self, player: PlayerData) -> bool:
		'''
		This whole function is why I want to use SQLite...
		'''
		with open("players.csv", newline='', encoding='utf-8') as f:
			reader = csv.DictReader(f)
			for row in reader:
				if row['id'] == '' or row['server_id'] == '':
					continue
				if int(row['id']) == player.id and int(row['server_id']) == player.server_id:
					return True
		return False

async def setup(bot):
	await bot.add_cog(Players(bot))
