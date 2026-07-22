import logging
import os

import discord

from discord.ext import commands
from dotenv import load_dotenv


class DDSBot(commands.Bot):
	def __init__(self):
		# Every permission needs to be enabled through intents.
		intents = discord.Intents.default()
		intents.message_content = True
		intents.members = True

		super().__init__(
			command_prefix=">",
			case_insensitive=True,
			intents=intents,
		)

		# Load the environment variables from the .env file.
		load_dotenv()
		self.token = os.getenv("DISCORD_TOKEN")

		# Remove built-in help command.
		self.remove_command("help")

		logging.basicConfig(level=logging.INFO)
		logging.getLogger("discord")

		file_handler = logging.FileHandler("bot_errors.log")
		file_handler.setLevel(logging.ERROR)
		logging.getLogger().addHandler(file_handler)

	async def setup_hook(self) -> None:
		await self.load_cogs()

	async def load_cogs(self):
		for file in os.listdir("./cogs"):
			if file.endswith(".py"):
				await self.load_extension(f"cogs.{file[:-3]}")

	async def on_ready(self):
		# self.user can be None in some runtime/type-checking scenarios, guard against that.
		name = self.user.name if self.user is not None else "Unknown"
		print(f"INFO: {name} has connected to Discord.")


bot = DDSBot()

if bot.token is not None:
	bot.run(bot.token)
else:
	print("ERROR: DISCORD TOKEN NOT SET")
