import discord

from discord.ext import commands

from helpers import checks, demon_queries, item_queries, player_queries
from shared_enums import DemonRegistration, Emotes


class Items(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.item_queries = item_queries.ItemQueries()
		self.player_queries = player_queries.PlayerQueries()
		self.demon_db = demon_queries.DemonQueries()

	@checks.has_profile()
	@commands.command(name="use", aliases=["u"], description="Use an item on a demon.")
	async def use_item_command(self, ctx, *, input_str: str) -> None:
		"""
		Use an item on a demon.

		Args:
			input_str (str): String containing item name and optional demon name, separated by a semicolon delimiter.
				"item_name; demon_name" or just "item_name" to use on selected demon.
		"""
		parts = input_str.split(";")
		item_name = parts[0].strip().title()
		demon_name = parts[1].strip().title() if len(parts) > 1 else None
		player = ctx.author
		server = ctx.guild
		item_id = self.item_queries.get_item_id_by_name(item_name)
		demon_id = None

		# Check if item is valid.
		if item_id is None:
			await ctx.send(f"The item **{item_name}** does not exist in your inventory.")
			return

		# Check if player has the item.
		if not self.item_queries.get_player_has_item(player.id, server.id, item_id):
			await ctx.send(f"You don't have any **{item_name}** in your inventory.")
			return

		# Get target demon ID.
		if demon_name:
			demon_id = self.demon_db.get_demon_id_by_name(demon_name)

			if demon_id is None:
				await ctx.send(f"A **{demon_name}** was not found in your party...")
				return
		else:
			demon_id = self.player_queries.get_selected_demon_id(player.id, server.id)

			# No demon was specified in command, and player doesn't have a demon selected.
			if demon_id is None:
				await ctx.send("You don't have a demon selected. Use `>select` to choose a demon first.")
				return

		# Check if in player's party.
		if await self.player_queries.check_demon_registration(player.id, server.id, demon_id) != DemonRegistration.IN_PARTY:
			await ctx.send(f"A **{demon_name}** was not found in your party...")
			return

		# Use the incense item and apply its effect.
		if self.item_queries.use_incense(player.id, server.id, demon_id, item_id):
			demon_name = self.demon_db.get_demon_name_by_id(demon_id)
			await ctx.send(
				(f"{player.mention} used **{item_name}** on **{demon_name}**!Their stored rank has **increased** by **3**."),
			)

	@checks.has_profile()
	@commands.command(name="inventory", aliases=["inv", "items"], description="View your item inventory.")
	async def item_inventory_command(self, ctx) -> None:
		"""View your item inventory."""
		player = ctx.author
		server = ctx.guild

		items = self.item_queries.get_player_items(player.id, server.id)

		if not items:
			await ctx.send("Your inventory is empty.")
			return

		view = ItemInventoryView(player.display_name, items)
		await ctx.send(view=view)


class ItemInventoryView(discord.ui.LayoutView):
	def __init__(self, player_name: str, items: dict[str, int], colour: int = 0xE93700) -> None:
		super().__init__()

		self.player_name = player_name
		self.items = items
		self.colour = colour

		self._build_item_inventory_layout()

	def _build_item_inventory_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=self.colour)
		tab = "\u2003"

		container.add_item(ui.TextDisplay(f"### {self.player_name}'s Item Inventory"))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(f"-# {Emotes.BLANK.value}{tab * 5}Name{tab * 5}Quantity"))

		max_width_name = 15
		max_width_qty = 3

		for name, qty in self.items.items():
			# emote = Emotes[name].value
			emote = Emotes.BLANK.value

			container.add_item(
				ui.TextDisplay(
					f"{emote}{tab}`{name.title():^{max_width_name}}`{tab * 2}`{qty:>{max_width_qty}}`",
				)
			)

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		self.add_item(container)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Items(bot))
