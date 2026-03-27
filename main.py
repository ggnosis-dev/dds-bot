import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio

# Load the environment variables from the .env file.
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Every permission needs to be enabled through intents.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)

@bot.event
async def on_ready():
	print(f'{bot.user} has connected to Discord!')


@bot.command(name='start', help="Sets up the player to start playing.")
async def start_command(ctx):
	'''
	Setup the player using a new PlayerData object. We'll then start and 'personal' encounter that is
	only available to the player, acting as a sort of tutorial and introduction.
	'''

	print(f'INFO: Setting up new player {ctx.author} with id {ctx.author.id} on server {ctx.guild.id}.')
	
	players_cog = bot.get_cog('Players')

	# If player setup is successful, begin the tutorial encounter.
	if await players_cog.setup_player(ctx):										# type: ignore
		await ctx.send("Starting your first encounter...")
		encounters_cog = bot.get_cog('Encounters')

		await encounters_cog.start_tutorial_encounter(ctx.channel, ctx.author)	# type: ignore


@bot.command(name='test', help="Spawns a test tutorial encounter in the current channel.")
async def test_spawn_command(ctx):
	encounters_cog = bot.get_cog('Encounters')
	await encounters_cog.start_tutorial_encounter(ctx.channel, ctx.author)		# type: ignore


async def load_cogs():
	async with bot:
		await bot.load_extension('cogs.players')
		await bot.load_extension('cogs.encounters')

		if token != None:
			await bot.start(token)

asyncio.run(load_cogs())
