import csv
import sqlite3

from database_paths import FUSION_CSV_PATH, PLAYERS_DB_PATH, ensure_db_dir_exists

ensure_db_dir_exists()

with open(FUSION_CSV_PATH, newline="") as f:
	reader = csv.reader(f)
	headers = next(reader)
	races = headers[1:]
	rows = list(reader)

	print(reader)
	print(f"HEADERS: {headers}")
	print(f"RACES: {races}")
	print(f"ROWS: {rows}")

	with sqlite3.connect(PLAYERS_DB_PATH) as conn:
		cursor = conn.cursor()

		# Delete existing demon table in case changes to general structure.
		cursor.execute("DROP TABLE IF EXISTS fusion_chart")

		# Create demon table.
		cursor.execute("""
			CREATE TABLE IF NOT EXISTS fusion_chart (
				race_1 TEXT NOT NULL,
				race_2 TEXT NOT NULL,
				race_result TEXT NOT NULL,
				PRIMARY KEY (race_1, race_2)
			)
		""")

		for i, row in enumerate(rows):
			race_1 = row[0]

			for j, result in enumerate(row[1:], start=0):
				print(f"INFO: i {i} j {j}")
				# Header and column are in the same order so this would be doubling up.
				# Skip empty cells too.
				if j < i or not result:
					print(f"Skipping. j < i: {j < i}. Result: {result}")
					continue

				race_2 = races[j]
				# race_1, race_2 = sorted([race_1, race_2])

				print(f"INFO: Putting in: {race_1} + {race_2}")

				cursor.execute(
					"""
					INSERT INTO fusion_chart (race_1, race_2, race_result)
					VALUES (?, ?, ?)
					""",
					(race_1, race_2, result),
				)
