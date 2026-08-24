import argparse
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

		# Remove built-in help command.
		self.remove_command("help")

		logging.basicConfig(level=logging.INFO)
		logging.getLogger("discord")

		file_handler = logging.FileHandler("bot_errors.log")
		file_handler.setLevel(logging.ERROR)
		logging.getLogger().addHandler(file_handler)

	def get_token(self, build_mode: bool) -> str | None:
		"""Load the environment variables from the .env file."""
		load_dotenv()
		return os.getenv("DISCORD_TOKEN") if build_mode else os.getenv("DEV_TOKEN")

	async def setup_hook(self) -> None:
		await self.load_cogs()

	async def load_cogs(self):
		"""Load every cog by dropping the .py in their path name."""
		for file in os.listdir("./cogs"):
			if file.endswith(".py"):
				await self.load_extension(f"cogs.{file[:-3]}")

	async def on_ready(self):
		# self.user can be None in some runtime/type-checking scenarios, guard against that.
		name = self.user.name if self.user is not None else "Unknown"
		print(f"INFO: {name} has connected to Discord.")


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-b", "--build", action="store_true", help="Build for the main 'DDS-Bot'. Without this, will start 'DDS-Bot Dev'."
	)
	args = parser.parse_args()

	bot = DDSBot()
	token = bot.get_token(args.build)

	if token is not None:
		bot.run(token)
	else:
		raise RuntimeError("ERROR: DISCORD TOKEN NOT SET")
