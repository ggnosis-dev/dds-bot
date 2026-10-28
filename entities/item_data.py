import json

from dataclasses import dataclass
from sqlite3 import Row

from shared_enums import Emotes


@dataclass
class ItemEntry:
	name: str
	quantity: int
	emote: Emotes
	description: str | None


@dataclass
class GemCost:
	gem_id: int
	amount: int
	name: str


@dataclass
class ShopItemData:
	item_id: int
	name: str
	item_type: str
	cost: list[GemCost]
	description: str
	emote: Emotes


@dataclass
class ShopItemGroup:
	name: str
	emote: Emotes
	description: str
	options: list[ShopItemData]


@dataclass
class ItemUseRules:
	min_rank: int
	max_rank: int
	race_locked: bool = True


INCENSE_RANK_INCREASE = 1
MINIMUM_COST = 500
MAX_RANK = 100
RANK_ITEM_RULES: dict[str, ItemUseRules] = {
	"sml_incense": ItemUseRules(min_rank=0, max_rank=30),
	"med_incense": ItemUseRules(min_rank=30, max_rank=60),
	"lrg_incense": ItemUseRules(min_rank=60, max_rank=90),
	"grimoire": ItemUseRules(min_rank=90, max_rank=100, race_locked=False),
}


def convert_row_to_item_entry(raw_row: Row) -> ItemEntry:
	try:
		row = dict(raw_row)

		return ItemEntry(
			name=row["name"],
			quantity=row["quantity"],
			emote=Emotes.GEM,
			description=row.get("description", "- No Description -"),
		)
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating ShopItemData | {e}")


def convert_rows_to_rags_item_data(rows: list[Row]) -> list[ShopItemData | ShopItemGroup]:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		entries: list[ShopItemData | ShopItemGroup] = []
		groups: dict[str, ShopItemGroup] = {}

		for raw_row in rows:
			row = dict(raw_row)
			cost = [GemCost(**c) for c in json.loads(row["cost"])]
			emote_name = row.get("emote") or "GEM"

			item_data = ShopItemData(
				item_id=row["item_id"],
				name=row["name"],
				item_type=row["type"],
				cost=cost,
				description=row["description"],
				emote=Emotes[emote_name],
			)

			# If no group, add it straight to entries.
			group_name = row.get("group_name")
			if group_name is None:
				entries.append(item_data)
				continue

			group = groups.get(group_name)
			# Create a new group if it doesn't exist.
			if group is None:
				group = ShopItemGroup(
					name=group_name,
					emote=Emotes[emote_name],
					description="",
					options=[],
				)
				groups[group_name] = group
				entries.append(group)

			# Add item_data to the group.
			group.options.append(item_data)

		return entries
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating ShopItemData | {e}")
