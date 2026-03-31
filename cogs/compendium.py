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

		total_number = await self.get_total_demon_count()
		comp_list = await self.check_compendium(user_id, guild_id)
		
		embed = CompendiumEmbed(ctx.author.name, comp_list or [], total_number)
		embed.create_compendium_embed()
		await ctx.send(embed = embed)


	async def get_total_demon_count(self) -> int:
		with sqlite3.connect('compendium.db') as conn:
			cursor = conn.cursor()
			result = cursor.execute('SELECT COUNT(*) FROM demons').fetchone()
			return result[0] if result else 0
		

	async def check_compendium(self, user_id: int, guild_id: int) -> list[dict] | None:
		with sqlite3.connect('players.db') as conn:
			# Attach the demon database to gain access to their data.
			conn.execute("ATTACH DATABASE 'compendium.db' AS demons_db")
			cursor = conn.cursor()

			# Retrieve the player's party.
			result = cursor.execute('''
				SELECT d.id, d.name, d.race, d.personality, pd.stored_rank
				FROM player_demons pd
				JOIN demons_db.demons d ON pd.demon_id = d.id
				WHERE pd.player_id = ? AND pd.server_id = ?
				ORDER BY d.race ASC, d.id ASC
			''', (user_id, guild_id)).fetchall()
			
			return result if result else None

class CompendiumEmbed(discord.Embed):
	def __init__(self, user_name: str, list: list[dict], total_number: int, page: int = 1, colour: int = 0xE93700):
		super().__init__(
			color = colour
		)
		self.user_name = user_name
		self.list = list
		self.page = page
		self.total_number = total_number


	def create_compendium_embed(self):
		line_break = '\u23AF\u23AF\u23AF#\u23AF\u23AF\u23AF'

		self.title = f"{self.user_name}'s Compendium"
		self.add_field(name = '', value = line_break, inline = False)

		# Create a set of collected demon IDs.
		collected_ids = {entry[0] for entry in self.list}

		# Cycle through the full list of demons.
		for i in range(1, self.total_number + 1):
			# If the demon was found, display its info. Else show it as unknown.
			if i in collected_ids:
				entry = next(entry for entry in self.list if entry[0] == i)
				name, race, personality, rank = entry[1], entry[2], entry[3], entry[4]
		
				self.add_field(
					name = '', 
					value = f"{EMOTES['icon']}\u000B\u000B{race}\u000B{name}\u000B\u000B`{rank}`\u000B\u000B{personality.title()}", 
					inline = False
				)
			else:
				self.add_field(
					name = '', 
					value = f"???", 
					inline = False
				)

		self.add_field(name = '', value = line_break)
		self.set_footer(text = f'Page {self.page}')


	def create_empty_party_embed(self):
		self.set_author(name = "Your party is empty!")


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Compendium(bot))
