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
class ShopItemData:
	item_id: int
	name: str
	item_type: str
	cost: dict
	description: str
	emote: Emotes


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


def convert_rows_to_shop_item_data(rows: list[Row]) -> list[ShopItemData]:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		entries = []
		for raw_row in rows:
			row = dict(raw_row)
			cost = json.loads(row["cost"])
			emote_name = row.get("emote") or "GEM"

			entries.append(
				ShopItemData(
					item_id=row["item_id"],
					name=row["name"],
					item_type=row["type"],
					cost=cost,
					description=row["description"],
					emote=Emotes[emote_name],
				)
			)

		return entries
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating ShopItemData | {e}")
