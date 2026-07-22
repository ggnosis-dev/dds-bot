import asyncio

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, TypeVar, cast

import discord

from discord.ext import commands

from shared_enums import Emotes


class HelpView(discord.ui.LayoutView):
	def __init__(
		self,
		bot: commands.Bot | commands.AutoShardedBot,
		entries: list,
		colour: int = 0xE93700,
	):
		super().__init__()

		self.bot = bot
		self.entries = entries
		self.colour = colour

		self.refresh()

	def refresh(self) -> None:
		self.clear_items()
		self._build_layout()

	def _build_layout(self) -> None:
		try:
			ui = discord.ui
			container = ui.Container(accent_color=self.colour)

			header_section = ui.Section(
				ui.TextDisplay(f"## `> DDS-BOT HELP SYSTEM` {Emotes['HUH'].value}"),
				accessory=ui.Thumbnail(
					media=self.bot.user.display_avatar.url,
				),
			)

			container.add_item(header_section)

			# for entry in self.entries:
			# 	lines = "\n".join(f"`{cmd['signature']}`: {cmd['help']}" for cmd in entry["commands"])
			# 	container.add_item(ui.TextDisplay(f"**{entry['name']}**\n{lines}"))

			self.add_item(container)
		except Exception as e:
			print(e)
