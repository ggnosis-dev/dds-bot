import sqlite3

from database_paths import DEMONS_DB_PATH, ensure_db_dir_exists


ensure_db_dir_exists()

demon_data = [
	# Name 				Race		Rank	Colour		Personality		Image URL
	('Pixie', 			'Fairy', 	5, 		0xE93700,	'CHEERFUL', 	'https://static.wikia.nocookie.net/megamitensei/images/b/b8/Pixie.GIF'),
	('Jack Frost',		'Fairy',	10, 	0x2A58CC, 	'CHEERFUL', 	'https://static.wikia.nocookie.net/megamitensei/images/a/ab/Jack_Frost.GIF'),
	('Dryad', 			'Fairy', 	12, 	0x9396E6, 	'SHY', 			'https://static.wikia.nocookie.net/megamitensei/images/2/23/Dryad.gif'),
	('Harpy', 			'Fairy', 	15, 	0x9396E6, 	'AGGRESSIVE', 	'https://static.wikia.nocookie.net/megamitensei/images/e/ee/Harpy2.GIF'),
	('Goblin', 			'Fairy', 	20, 	0xE93700, 	'AGGRESSIVE', 	'https://static.wikia.nocookie.net/megamitensei/images/b/ba/Goblin.GIF'),
	('Troll', 			'Fairy', 	25, 	0x2A58CC, 	'AGGRESSIVE', 	'https://static.wikia.nocookie.net/megamitensei/images/2/2f/Troll.GIF'),
	('Elf', 			'Fairy', 	30, 	0x9396E6, 	'SHY', 			'https://static.wikia.nocookie.net/megamitensei/images/7/77/Elf.GIF'),
	('Minotaur', 		'Beast', 	27, 	0xE93700, 	'AGGRESSIVE', 	'https://static.wikia.nocookie.net/megamitensei/images/f/f5/Minotaur.GIF'),
	('Medusa', 			'Femme', 	39, 	0x2A58CC, 	'AGGRESSIVE', 	'https://static.wikia.nocookie.net/megamitensei/images/f/fe/Medusa_02.GIF'),
	('Loki', 			'Vile', 	50, 	0x9396E6, 	'CHEERFUL', 	'https://static.wikia.nocookie.net/megamitensei/images/d/d7/Loki.GIF'),
	('Loki (Paradox)', 	'Vile', 	60, 	0x9396E6, 	'CHEERFUL', 	'https://static.wikia.nocookie.net/megamitensei/images/f/f2/Loki4.GIF'),
]

with sqlite3.connect(DEMONS_DB_PATH) as conn:
	cursor = conn.cursor()

	# Delete existing demon table in case changes to general structure.
	cursor.execute('DROP TABLE IF EXISTS demons')

	# Create demon table.
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS demons (
			id INTEGER PRIMARY KEY,
			name TEXT,
			race TEXT,
			rank INTEGER,
			colour INTEGER,
			personality TEXT,
			image_url TEXT
		)
	''')

	# Insert demon data.
	cursor.executemany('''
		INSERT INTO demons (name, race, rank, colour, personality, image_url) 
		VALUES (?, ?, ?, ?, ?, ?)
	''', demon_data)