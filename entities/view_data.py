from dataclasses import dataclass


@dataclass
class ColumnConfig:
	# Key should match the database column's name.
	key: str
	label: str
	width: int = 0
	header_tabs: int = 1
	align: str = "^"
