import discord
import typing

from cogs.demons import DemonData, DemonQueries
from discord.ext import commands
from helpers import checks, item_queries, players
from shared_enums import Emotes



class Items(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.item_queries = item_queries.ItemQueries()
		self.player_queries = players.Players()
		self.demon_queries = DemonQueries()


	@checks.has_profile()
	@commands.command(name = 'use', aliases = ['u'], description = "Use an item on a demon.")
	async def use_item_command(self, ctx, *, item_name: str) -> None:
		'''Use an item on a demon.'''
		player = ctx.author
		server = ctx.guild
		item_id = self.item_queries.get_item_id_by_name(item_name)
		
		if item_id is None:
			await ctx.send(f"The item '{item_name}' does not exist...")
			return

		if self.item_queries.get_player_has_item(player.id, server.id, item_id) == False:
			await ctx.send(f"You don't have any {item_name} in your inventory.")
			return
		
		selected_demon_id = self.player_queries.get_selected_demon_id(player.id, server.id)
		
		if selected_demon_id is None:
			await ctx.send("You don't have a demon selected. Use `>select` to choose a demon first.")
			return
		
		if self.item_queries.use_incense(
			player.id, 
			server.id, 
			selected_demon_id,
			item_id
		):
			demon_data = typing.cast(DemonData, self.demon_queries.get_demon_by_id(selected_demon_id))
			await ctx.send(f"{player.mention} used {item_name} on {demon_data.name}! Their stored rank has increased by 3.")

	@checks.has_profile()
	@commands.command(name = 'inventory', aliases = ['inv'], description = "View your item inventory.")
	async def item_inventory_command(self, ctx) -> None:
		'''View your item inventory.'''
		print("HERE")
		player = ctx.author
		server = ctx.guild

		items = self.item_queries.get_player_items(player.id, server.id)

		if not items:
			await ctx.send("Your inventory is empty.")
			return
		
		view = ItemInventoryView(player.display_name, items)
		await ctx.send(view = view)


class ItemInventoryView(discord.ui.LayoutView):
	def __init__(
		self, 
		player_name: str, 
		items: dict[str, int],
		colour: int = 0xE93700
	) -> None:
		super().__init__()

		self.player_name = player_name
		self.items = items
		self.colour = colour

		self._build_item_inventory_layout()


	def _build_item_inventory_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color = self.colour)
		tab = '\u2003'

		container.add_item(ui.TextDisplay(f"### {self.player_name}'s Item Inventory"))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay(
			f"-# {Emotes.BLANK.value}{tab * 5}Name{tab * 5}Quantity")
		)

		max_width_name = 15
		max_width_qty = 3

		# Item: fairy_incense, Quantity: {'display_name': 'Fairy Incense', 'description': "Increase a Fairy's rank by a little bit.", 'exlusive_to': 'Fairy', 'cost': {'AMETHYST': 3, 'AGATE': 2}}
		for name, qty in self.items.items():
			print(f"Item: {name}, Quantity: {qty}")
			# emote = Emotes[name].value
			emote = Emotes.BLANK.value

			container.add_item(ui.TextDisplay(
				f"{emote}{tab}`{name.title():^{max_width_name}}`{tab * 2}`{qty:>{max_width_qty}}`", 
			))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		self.add_item(container)


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Items(bot))
