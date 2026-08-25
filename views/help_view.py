import re

from typing import cast

import discord

from discord.ext import commands

from entities.view_data import HELP_PAGE_SIZE
from shared_enums import EmbedColours, Emotes
from views.common_view import BaseLayoutView


class HelpView(BaseLayoutView[dict]):
	"""Code is very much based off the shop menu."""

	def __init__(
		self,
		entries: list[dict],
		bot: commands.Bot | commands.AutoShardedBot,
		colour: int = EmbedColours.DEFAULT.value,
	):
		super().__init__(entries, page_size=HELP_PAGE_SIZE, colour=colour)

		self.entries = entries
		self.bot = bot

		# Expanding a cog will show us its commands. Should only ever be one at a time because messages are
		# limited to 4000 characters or something.
		self.expanded_cog: str | None = None

		self.refresh()

	class SectionButton(discord.ui.Button):
		"""Custom button for showing more information in a view."""

		def __init__(self, entry: dict, expanded: bool) -> None:
			self.entry = entry

			super().__init__(
				label="ⓘ ◥" if expanded else "ⓘ ◢",
				style=discord.ButtonStyle.secondary,
			)

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when the information button is clicked. Allows wrapping around the pages."""

			view = cast(HelpView, self.view)

			# Toggle the section that is currently open.
			if view.expanded_cog == self.entry["name"]:
				view.expanded_cog = None
			else:
				view.expanded_cog = self.entry["name"]

			view.refresh()
			await interaction.response.edit_message(view=view)

	def refresh(self) -> None:
		self.clear_items()
		self._build_layout()

	def _build_layout(self) -> None:
		try:
			page_entries = self._get_page_entries()

			container = discord.ui.Container(accent_color=self.colour)
			container = self._build_header(container)

			for entry in page_entries:
				expanded = bool(self.expanded_cog == entry["name"])
				container = self._build_page_entry(container, entry, expanded)

			container = self._build_footer(container)

			self.add_item(container)
		except Exception as e:
			print(e)

	def _build_header(self, container: discord.ui.Container) -> discord.ui.Container:
		bot_user = self.bot.user

		if bot_user is None:
			raise RuntimeError(
				"ERROR: Bot user was None, which shouldn't happen but to get linter to stop complaining, I will do a check."
			)

		section = discord.ui.Section(
			discord.ui.TextDisplay(f"{Emotes.BLANK.value}\n## `> DDS-BOT HELP SYSTEM` {Emotes['HUH'].value}"),
			accessory=discord.ui.Thumbnail(media=bot_user.display_avatar.url),
		)
		container.add_item(section)
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
		return container

	def _build_page_entry(self, container: discord.ui.Container, entry: dict, expanded: bool) -> discord.ui.Container:
		cog_section_btn = self.SectionButton(entry, expanded)
		cog_name = re.sub(r"(?<!^)(?=[A-Z])", " ", entry["name"])
		cog_desc = entry["cog_desc"]

		section = discord.ui.Section(
			discord.ui.TextDisplay(f"**{cog_name}** - {cog_desc}"),
			accessory=cog_section_btn,
		)
		container.add_item(section)

		if expanded:
			for cmd in entry["commands"]:
				usage = cmd["usage"]
				hlp = cmd["help"]

				container.add_item(discord.ui.TextDisplay(f"-# `{usage}`:\n{hlp}"))
				container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

		return container
