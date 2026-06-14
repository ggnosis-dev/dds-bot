import typing

import discord

from discord.ext import commands

from helpers import checks
from helpers.views import ConfirmationView, MessageView
from queries import demon_queries, player_queries
from shared_enums import DemonRegistration, Emotes

## Constants
PAGE_SIZE = 5


class Party(commands.Cog):
	"""Cog for viewing and managing player parties."""

	def __init__(self, bot: commands.Bot):
		"""Init the Party cog with reference to bot instance and database classes."""
		self.bot = bot
		self.player_db = player_queries.PlayerQueries()

	@checks.has_profile()
	@commands.command(name="party", aliases=["p"], help="Displays the player's current party.")
	async def party_command(self, ctx: commands.Context, mentioned: discord.Member | None = None) -> None:
		"""
		Command to display player's current party.

		Args:
			ctx (discord.Context): Context of the command call.
			mentioned (discord.Member | None): Optional user to check party for.
		"""
		guild = typing.cast(discord.Guild, ctx.guild)
		player = mentioned if mentioned is not None else ctx.author

		party_list = await self.player_db.check_party(player.id, guild.id)
		selected_demon_id = self.player_db.get_selected_demon_id(player.id, guild.id)  # type: ignore

		view = PartyView(player.name, party_list, selected_demon_id)
		await ctx.send(view=view)

	@checks.has_profile()
	@commands.command(name="release", aliases=["rel"], help="Release a demon from your party.")
	async def release_command(self, ctx: commands.Context, *, demon_name: str) -> None:
		"""
		Command to release a demon from the player's party.

		Args:
			ctx (discord.Context): Context of the command call.
			demon_name (str): Name of the demon to release from the party. The * before it in the arguments
				allows for multi-word demon names.
		"""
		guild = typing.cast(discord.Guild, ctx.guild)
		player = ctx.author
		demon_name = demon_name.title()
		demon_id = demon_queries.get_demon_id_by_name(demon_name)

		if demon_id is None:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Check if demon is in party.
		in_party = await self.player_db.check_demon_registration(player.id, guild.id, demon_id)

		if in_party != DemonRegistration.IN_PARTY:
			msg = MessageView(f"A **{demon_name}** was not found in your party...")
			await ctx.send(view=msg)
			return

		# Send a confirmation view.
		view = ConfirmationView(f"Are you sure you want to release **{demon_name}**?", confirmLabel="Yes", denyLabel="No")
		result = await ConfirmationView.send_message(view, ctx)

		if result is False or result is None:
			return

		await self.player_db.set_demon_in_party(player.id, guild.id, demon_id, party_add=False)
		msg = MessageView(
			f"### Good-Bye...\n**{demon_name}** will have a happy life in a faraway forest."
			f"You will never see your **{demon_name}** again."
		)
		await ctx.send(view=msg)


class PartyView(discord.ui.LayoutView):
	"""Custom view for displaying the player's party."""

	def __init__(
		self,
		user_name: str,
		list: list[dict],
		selected_demon_id: int | None = None,
		page: int = 1,
		colour: int = 0xE93700,
	) -> None:
		"""
		Init for the party view. Builds the layout based on whether the player's party is empty or not.

		Args:
			user_name (str): Name of the user whose party is being displayed.
			list (list[dict]): List of demons in the player's party. Each dict includes ID, name, race, and stored_rank.
			page (int): Current page number of the party view. Defaults to 1.
			colour (int): Colour of the party view.
		"""
		super().__init__()

		self.user_name = user_name
		self.list = list
		self.selected_demon_id = selected_demon_id
		self.page = page
		self.colour = colour

		self._build_party_layout() if list else self._build_party_empty_layout()

	class PageButton(discord.ui.Button):
		"""Custom button for navigating between pages of the party view."""

		def __init__(self, direction: str) -> None:
			if direction == "prev":
				super().__init__(label="<", style=discord.ButtonStyle.primary)
			elif direction == "next":
				super().__init__(label=">", style=discord.ButtonStyle.primary)
			else:
				raise ValueError("ERROR: Direction must be 'prev' or 'next'.")

		async def callback(self, interaction: discord.Interaction) -> None:
			"""Callback for when a page navigation button is clicked. Allows wrapping around the pages."""
			view = typing.cast(PartyView, self.view)

			if self.label == "<":
				view.page = view.total_pages if view.page <= 1 else view.page - 1
			elif self.label == ">":
				view.page = 1 if view.page >= view.total_pages else view.page + 1

			view.clear_items()
			view._build_party_layout()
			await interaction.response.edit_message(view=view)

	def _build_party_layout(self) -> None:
		"""Function to build the party view layout."""
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)
		tab = "\u2003"
		page_entries = self._get_page_entries()
		page_nav = ui.ActionRow(self.PageButton("prev"), self.PageButton("next"))
		max_width_race = 8
		max_width_name = 12
		max_width_rank = 3

		container.add_item(ui.TextDisplay(f"### {self.user_name}'s Party"))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f"-# {Emotes.BLANK.value}{tab * 3}Race{tab * 5}Name{tab * 4}Rank"))

		# Only render selected if first page and selected has been passed in.
		if self.selected_demon_id is not None and self.page == 1:
			selected_demon = None

			# Find the selected demon if it exists in the list.
			for entry in self.list:
				if entry[0] != self.selected_demon_id:
					continue

				selected_demon = entry
				break

			# Draw selected demon at the top of the list on the first page.
			if selected_demon:
				_id, name, race, rank = selected_demon

				container.add_item(
					ui.TextDisplay(
						f"{Emotes.ONE.value}{tab}`{race:^{max_width_race}}`{tab}`{name:^{max_width_name}}`{tab}`{rank:>{max_width_rank}}`",
					)
				)

		# Draw the rest of the demons on the current page.
		for entry in page_entries:
			id, name, race, rank = entry

			if id == self.selected_demon_id:
				continue

			container.add_item(
				ui.TextDisplay(
					f"{Emotes.ICON.value}{tab}`{race:^{max_width_race}}`{tab}`{name:^{max_width_name}}`{tab}`{rank:>{max_width_rank}}`",
				)
			)

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f"-# Page {self.page} of {self.total_pages}"))
		container.add_item(page_nav)

		self.add_item(container)

	def _build_party_empty_layout(self) -> None:
		"""Function to build the party view layout when it's empty."""
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)
		container.add_item(ui.TextDisplay("Your party is empty!"))
		self.add_item(container)

	def _get_page_entries(self) -> list[dict]:
		"""
		Helper function to get the entries to be displayed on the current page of the party view.
		Sets self.total_pages based on the number of entries.

		Returns:
			list[dict]: List of demon entries to be displayed on the current page.
		"""
		self.total_pages = int(max(1, (len(self.list) + PAGE_SIZE - 1) / PAGE_SIZE))
		self.page = max(1, min(self.page, self.total_pages))

		start_index = (self.page - 1) * PAGE_SIZE
		end_index = start_index + PAGE_SIZE

		# Use delimiter to slice out entries.
		return self.list[start_index:end_index]


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Party(bot))
