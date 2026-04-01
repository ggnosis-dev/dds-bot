import discord
import sqlite3
import json

from discord.ext import commands

# TODO: Move this and import it here and in encounters.
from cogs.encounters import EMOTES

class Party(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name='party', help="Displays the player's current party.")
	async def party_command(self, ctx: commands.Context, user_id: int = -1):
		if ctx.guild is None : return

		guild_id = ctx.guild.id

		if user_id == -1:
			user_id = ctx.author.id

		party_list = await self.check_party(user_id, guild_id)

		if party_list is None:
			embed = PartyEmbed(ctx.author.name, [])
			embed.create_empty_party_embed()
			await ctx.send(embed = embed)
			return
		
		embed = PartyEmbed(ctx.author.name, party_list)
		embed.create_party_embed()
		await ctx.send(embed = embed)


	@commands.command(name = 'release', aliases = ['r'], help = "Release a demon from your party.")
	async def release_command(self, ctx: commands.Context, *, demon_name: str):
		if ctx.guild is None : return
		
		demon_name = demon_name.title()
		demon_cog = self.bot.get_cog('Demon')
		demon_id = demon_cog.get_demon_id_by_name(demon_name)	# type: ignore

		if demon_id != -1:
			players_cog = self.bot.get_cog('Players')

			await players_cog.set_demon_in_party(ctx.author.id, ctx.guild.id, demon_id, False)	# type: ignore
			await ctx.send(f"You have released {demon_name} from your party...")
			return
		await ctx.send(f"The demon {demon_name} was not found in your party. Did you spell their name correctly?")


	async def check_party(self, user_id: int, guild_id: int) -> list[dict] | None:
		with sqlite3.connect('players.db') as conn:
			# Attach the demon database to gain access to their data.
			conn.execute("ATTACH DATABASE 'compendium.db' AS demons_db")
			cursor = conn.cursor()

			# Retrieve the player's party.
			result = cursor.execute('''
				SELECT d.id, d.name, d.race, pd.stored_rank
				FROM player_demons pd
				JOIN demons_db.demons d ON pd.demon_id = d.id
				WHERE pd.player_id = ? AND pd.server_id = ? AND pd.in_party = 1
				ORDER BY d.race ASC, d.id ASC
			''', (user_id, guild_id)).fetchall()
			
			return result if result else None

class PartyEmbed(discord.Embed):
	def __init__(self, user_name: str, list: list[dict], page: int = 1, colour: int = 0xE93700):
		super().__init__(
			color = colour
		)
		self.user_name = user_name
		self.list = list
		self.page = page


	def create_party_embed(self):
		line_break = '\u23AF\u23AF\u23AF#\u23AF\u23AF\u23AF'

		self.title = f"{self.user_name}'s Party"
		self.add_field(name = '', value = line_break, inline = False)

		for entry in self.list:
			name, race, rank = entry[1], entry[2], entry[3]

			self.add_field(
				name = '', 
				value = f"{EMOTES['icon']}\u000B\u000B{race}\u000B\u000B{name}\u000B\u000B\u000B\u000B`{rank}`", 
				inline = False
			)

		self.add_field(name = '', value = line_break)
		self.set_footer(text = f'Page {self.page}')


	def create_empty_party_embed(self):
		self.set_author(name = "Your party is empty!")


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Party(bot))
