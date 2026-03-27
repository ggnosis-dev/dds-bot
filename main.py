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

bot = commands.Bot(command_prefix='#', intents=intents)

@bot.event
async def on_ready():
	print(f'{bot.user} has connected to Discord!')


@bot.command(name='test', aliases=["t"], help='This is a test command.')
async def command_name(ctx):
	await ctx.send("This is a test")

async def load_cogs():
	async with bot:
		await bot.load_extension('cogs.encounters')

		if token != None:
			await bot.start(token)

asyncio.run(load_cogs())
