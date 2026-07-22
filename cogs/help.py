from discord.ext import commands

from views.help_view import HelpView


class HelpOverwrite(commands.HelpCommand):
	async def send_bot_help(self, mapping):
		try:
			entries = []

			for cog, cmds in mapping.items():
				filtered = await self.filter_commands(cmds, sort=True)

				if not filtered:
					continue

				cog_entry = {
					"name": cog.qualified_name if cog is not None else "NONE",
					"commands": (
						{
							"signature": self.get_command_signature(cmd),
							"help": cmd.help,
							"usage": cmd.usage,
							"aliases": cmd.aliases,
						}
						for cmd in filtered
					),
				}

				entries.append(cog_entry)

			channel = self.get_destination()
			view = HelpView(bot=self.context.bot, entries=entries)
			await channel.send(view=view)
		except Exception as e:
			print(e)


async def setup(client):
	client._default_help_command = client.help_command
	client.help_command = HelpOverwrite()


async def teardown(client):
	client.help_command = client._default_help_command
