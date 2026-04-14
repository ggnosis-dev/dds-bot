import asyncio
import discord
import os

from discord.ext import commands
from dotenv import load_dotenv

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


async def load_cogs():
	async with bot:
		await bot.load_extension('cogs.encounters')
		await bot.load_extension('cogs.party')
		await bot.load_extension('cogs.compendium')

		if token != None:
			await bot.start(token)

asyncio.run(load_cogs())
