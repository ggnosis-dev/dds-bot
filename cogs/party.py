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
		print(f'INFO: Displaying party for player {ctx.author} with id {user_id} on server {ctx.guild}.')
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


	async def check_party(self, user_id: int, guild_id: int) -> list[dict] | None:
		print(f'INFO: Checking party for player with id {user_id} on server {guild_id}.')
		conn = sqlite3.connect('players.db')
		cursor = conn.cursor()

		cursor.execute('''
			SELECT party FROM players 
				WHERE id = ? AND server_id = ?
		''', (user_id, guild_id))
		result = cursor.fetchone()
		
		if result is None: 
			conn.close()
			return None

		party_object = json.loads(result[0])

		if len(party_object) == 0:
			conn.close()
			return None
		
		print(f'INFO: Retrieved party JSON for player with id {user_id} on server {guild_id}: {party_object}')
		
		# Create tuple of the demon IDs.
		demon_ids = tuple(entry['id'] for entry in party_object)
		
		# Create a string of question marks for the SQL query.
		query_placeholders = ','.join('?' * len(demon_ids))

		print(demon_ids)

		print(f'DEBUG: query_placeholders={query_placeholders}, demon_ids={demon_ids}')
		cursor.execute(f'''
			SELECT id, race, name FROM demons 
				WHERE id IN ({query_placeholders})
		''', demon_ids)

		demon_data = cursor.fetchall()
		print(demon_data)
		conn.close()

		name_map = {}
		for row in demon_data:
			demon_id = row[0]
			demon_race = row[1]
			demon_name = row[2]
			name_map[demon_id] = (demon_race, demon_name)
		
		party = []
		for entry in party_object:
			demon_id = entry['id']
			demon_rank = entry['rank']
			demon_race, demon_name = name_map.get(demon_id, ('Unknown', 'Unknown'))
			party.append({
				'id': demon_id,
				'race': demon_race,
				'name': demon_name,
				'rank': demon_rank,
			})

		print(f'INFO: Retrieved party for player with id {user_id} on server {guild_id}: {party}')

		return party

class PartyEmbed(discord.Embed):
	def __init__(self, user_name: str, list: list[dict], page: int = 1, colour: int = 0xE93700):
		super().__init__(
			color = colour
		)
		self.user_name = user_name
		self.list = list
		self.page = page


	def create_party_embed(self):
		print(f'INFO: Creating party embed for {self.user_name} with party {self.list}.')

		self.title = f"{self.user_name}'s Party"

		for entry in self.list:
			self.add_field(
				name = '', 
				value = f"{entry['id']}\t`{entry['rank']}`", 
				inline = False
			)

		# self.set_image(url = small_image_url)
		self.set_footer(text = f'Page {self.page}')


	def create_empty_party_embed(self):
		self.set_author(name = "Your party is empty!")


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Party(bot))
