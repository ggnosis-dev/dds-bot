import csv
import sqlite3

from database_paths import FUSION_CSV, PLAYERS_DB_PATH

with open(FUSION_CSV, newline="") as f:
	reader = csv.reader(f)

	# Top row is a list of races (skip 1 due to blank cell).
	headers = next(reader)
	races = headers[1:]
	rows = list(reader)

	with sqlite3.connect(PLAYERS_DB_PATH) as conn:
		cursor = conn.cursor()

		# Delete existing demon table in case changes to general structure.
		cursor.execute("DROP TABLE IF EXISTS fusion_chart")

		# Create fusion chart table.
		cursor.execute("""
			CREATE TABLE IF NOT EXISTS fusion_chart (
				race_1 TEXT NOT NULL,
				race_2 TEXT NOT NULL,
				race_result TEXT NOT NULL,
				PRIMARY KEY (race_1, race_2)
			)
		""")

		# For every row, keeping track of the row index...
		for i, row in enumerate(rows):
			# e.g. ['Fairy', '', 'Element', '', '', '', 'Jaki', '', '']
			# Index 0 will be the first ingredient in the fusion, the left-most entry/name in the chart.
			race_1 = row[0]

			# For every potential "result" that the first race can turn into...
			for j, result in enumerate(row[1:]):
				# Header and column are in the same order so this would be doubling up. Skip empty cells too.
				if j < i or not result:
					print(f"WARN: Skipping: {race_1} + {races[j]} = {result or 'N/A'}. i ({i}) | j ({j})")
					continue

				# j is the position of the result, so races[j] will be the race in the header.
				race_2 = races[j]

				print(f"INFO: Putting in {race_1} + {race_2} = {result}")

				cursor.execute(
					"""
					INSERT INTO fusion_chart (race_1, race_2, race_result)
					VALUES (?, ?, ?)
					""",
					(race_1, race_2, result),
				)
