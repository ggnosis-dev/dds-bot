from discord.ext import commands

from entities.command_data import COG_DESCRIPTIONS
from views.help_view import HelpView


class HelpOverwrite(commands.HelpCommand):
	async def send_bot_help(self, mapping):
		try:
			entries = []
			print(mapping)

			for cog, cmds in mapping.items():
				filtered = await self.filter_commands(cmds, sort=True)

				if not filtered or cog is None:
					continue

				cog_name = cog.qualified_name
				cog_desc = COG_DESCRIPTIONS[cog_name]
				cog_cmds = (
					{
						"signature": self.get_command_signature(cmd),
						"help": cmd.help,
						"usage": cmd.usage,
						"aliases": cmd.aliases,
					}
					for cmd in filtered
				)

				cog_entry = {
					"name": cog_name,
					"cog_desc": cog_desc,
					"commands": cog_cmds,
				}

				entries.append(cog_entry)

			channel = self.get_destination()
			view = HelpView(entries=entries)
			await channel.send(view=view)
		except Exception as e:
			print(f"ERROR: send_bot_help | {e}")


async def setup(client):
	client._default_help_command = client.help_command
	client.help_command = HelpOverwrite()


async def teardown(client):
	client.help_command = client._default_help_command
