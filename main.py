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


@bot.command(name='test', aliases=["t"], help='This is a test command.')
async def command_name(ctx):
	await ctx.send("This is a test")

@bot.command(name='start', help="Sets up the player to start playing.")
async def start_command(ctx):
	'''
	Setup the player using a new PlayerData object. We'll then start and 'personal' encounter that is
	only available to the player, acting as a sort of tutorial and introduction.
	'''
	print(f'Setting up player {ctx.author} with id {ctx.author.id} on server {ctx.guild} with id {ctx.guild.id}')
	players_cog = bot.get_cog('Players')

	if players_cog is None:
		await ctx.send("Sorry, there was an error setting up your profile. Please try again later.")
		return

	if await players_cog.setup_player(ctx):
		encounters_cog = bot.get_cog('Encounters')

		if encounters_cog is None:
			await ctx.send("Sorry, there was an error starting your encounter. Please try again later.")
			return

		await encounters_cog.start_encounter(ctx.channel.id, force_demon_id=1)


async def load_cogs():
	async with bot:
		await bot.load_extension('cogs.players')
		await bot.load_extension('cogs.encounters')

		if token != None:
			await bot.start(token)

asyncio.run(load_cogs())
