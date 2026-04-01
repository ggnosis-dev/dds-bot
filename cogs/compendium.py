import discord
import sqlite3
import json

from discord.ext import commands

# TODO: Move this and import it here and in encounters.
from cogs.encounters import EMOTES

class Compendium(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name = 'compendium', aliases = ['comp', 'c'], help = "Displays the player's compendium.")
	async def compendium_command(self, ctx: commands.Context, user_id: int = -1):
		if ctx.guild is None : return

		guild_id = ctx.guild.id

		if user_id == -1:
			user_id = ctx.author.id

		comp_list = await self.check_compendium(user_id, guild_id)
		
		embed = CompendiumEmbed(ctx.author.name, comp_list)
		embed.create_compendium_embed()
		await ctx.send(embed = embed)
	

	@commands.command(name = 'summon', aliases = ['s'], help = "Summon a demon from the player's compendium.")
	async def summon_command(self, ctx, *, demon_name):
		# Check the player has the demon in compendium. 
		# Make sure it's not in the party already. This only really is an issue when we introduce money.
		# Use set_demon_in_party to True
		if ctx.guild is None : return
		
		demon_name = demon_name.title()
		demon_cog = self.bot.get_cog('Demon')
		demon_id = demon_cog.get_demon_id_by_name(demon_name)	# type: ignore

		if demon_id != -1:
			players_cog = self.bot.get_cog('Players')

			await players_cog.set_demon_in_party(ctx.author.id, ctx.guild.id, demon_id, True)	# type: ignore
			await ctx.send(f"You have summoned {demon_name} to your party...")
			return
		await ctx.send(f"A demon with the name {demon_name} was not found in your compendium.")


	async def check_compendium(self, user_id: int, guild_id: int) -> list[dict]:
		with sqlite3.connect('players.db') as conn:
			# Attach the demon database to gain access to their data.
			conn.execute("ATTACH DATABASE 'compendium.db' AS demons_db")
			cursor = conn.cursor()

			# Use LEFT JOIN to get all demons. stored_rank will be NULL if player hasn't encountered them.
			result = cursor.execute('''
				SELECT d.id, d.name, d.race, d.personality, pd.stored_rank, pd.in_party
				FROM demons_db.demons d
				LEFT JOIN player_demons pd ON pd.demon_id = d.id
					AND pd.player_id = ? AND pd.server_id = ?
				ORDER BY d.race ASC, d.id ASC
			''', (user_id, guild_id)).fetchall()

			return result

class CompendiumEmbed(discord.Embed):
	def __init__(self, user_name: str, list: list[dict], page: int = 1, colour: int = 0xE93700):
		super().__init__(
			color = colour
		)
		self.user_name = user_name
		self.list = list
		self.page = page


	def create_compendium_embed(self):
		line_break = '\u23AF\u23AF\u23AF#\u23AF\u23AF\u23AF'

		self.title = f"{self.user_name}'s Compendium"
		self.add_field(name = '', value = line_break, inline = False)

		for entry in self.list:
			_demon_id, name, race, personality, rank, in_party = entry

			# This will exist if the player has encountered.
			if rank is not None:
				emote = EMOTES['icon'] if in_party else EMOTES['blank']

				self.add_field(
					name = '', 
					value = f"{emote}\u000B\u000B{race}\u000B\u000B{name}\u000B\u000B\u000B\u000B`{rank}`\u000B\u000B{personality.title()}", 
					inline = False
				)
			else:
				self.add_field(
					name = '', 
					value = f"{EMOTES['blank']}\u000B\u000B{race}\u000B\u000B?????\u000B\u000B\u000B\u000B`???`\u000B\u000B?????", 
					inline = False
				)
		self.add_field(name = '', value = line_break)
		self.set_footer(text = f'Page {self.page}')


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Compendium(bot))
