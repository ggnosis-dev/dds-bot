import sqlite3

from database_paths import PLAYERS_DB_PATH
from helpers.demon_queries import DemonData, DemonQueries


class FusionQueries:
	def _get_db_connection(self) -> sqlite3.Connection:
		"""Helper method to get a connection to the players database."""
		conn = sqlite3.connect(PLAYERS_DB_PATH)

		# Enforce foreign key constraints for the connection.
		conn.execute("PRAGMA foreign_keys = ON")
		return conn

	def get_fused_race(self, race_1: str, race_2: str) -> str | None:
		# Database has race_1 in alphabetically order.
		race_1, race_2 = sorted([race_1, race_2])

		with self._get_db_connection() as conn:
			cursor = conn.cursor()

			race_result = cursor.execute(
				"""
				SELECT race_result FROM fusion_chart
				WHERE race_1 = ? AND race_2 = ?
				""",
				(race_1, race_2),
			).fetchone()

			return race_result[0] if race_result else None

	def get_fused_demon(self, race_1: str, race_2: str, average_rank: int) -> DemonData | None:
		fused_race = self.get_fused_race(race_1, race_2)

		# Some races won't fuse together deliberately.
		if not fused_race:
			print(f"INFO: {race_1} + {race_2} cannot fuse together.")
			return None

		if fused_race.lower() == "element":
			print("WARN: Element fusion is not yet implemented.")
			return None

		return DemonQueries().get_closest_demon_in_race(fused_race, average_rank)
