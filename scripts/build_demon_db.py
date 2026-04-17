import sqlite3

from database_paths import PLAYERS_DB_PATH, ensure_db_dir_exists
from shared_enums import GemList, Personality

ensure_db_dir_exists()

demon_data = [
	# Name 				Race		Rank	Colour		Personality						Gem							Image URL
	('Pixie', 			'Fairy', 	5, 		0xE93700,	Personality.CHEERFUL.name, 		GemList.AMETHYST.name,		'https://static.wikia.nocookie.net/megamitensei/images/b/b8/Pixie.GIF'),
	('Jack Frost',		'Fairy',	10, 	0x2A58CC, 	Personality.CHEERFUL.name, 		GemList.AQUAMARINE.name,	'https://static.wikia.nocookie.net/megamitensei/images/a/ab/Jack_Frost.GIF'),
	('Dryad', 			'Fairy', 	12, 	0x9396E6, 	Personality.SHY.name, 			GemList.EMERALD.name,		'https://static.wikia.nocookie.net/megamitensei/images/2/23/Dryad.gif'),
	('Harpy', 			'Fairy', 	15, 	0x9396E6, 	Personality.AGGRESSIVE.name, 	GemList.GARNET.name, 		'https://static.wikia.nocookie.net/megamitensei/images/e/ee/Harpy2.GIF'),
	('Goblin', 			'Fairy', 	20, 	0xE93700, 	Personality.AGGRESSIVE.name, 	GemList.OPAL.name, 			'https://static.wikia.nocookie.net/megamitensei/images/b/ba/Goblin.GIF'),
	('Troll', 			'Fairy', 	25, 	0x2A58CC, 	Personality.AGGRESSIVE.name, 	GemList.TOPAZ.name, 		'https://static.wikia.nocookie.net/megamitensei/images/2/2f/Troll.GIF'),
	('Elf', 			'Fairy', 	30, 	0x9396E6, 	Personality.SHY.name, 			GemList.TURQUOISE.name,		'https://static.wikia.nocookie.net/megamitensei/images/7/77/Elf.GIF'),
	('Minotaur', 		'Beast', 	27, 	0xE93700, 	Personality.AGGRESSIVE.name, 	GemList.ONYX.name, 			'https://static.wikia.nocookie.net/megamitensei/images/f/f5/Minotaur.GIF'),
	('Medusa', 			'Femme', 	39, 	0x2A58CC, 	Personality.AGGRESSIVE.name, 	GemList.RUBY.name, 			'https://static.wikia.nocookie.net/megamitensei/images/f/fe/Medusa_02.GIF'),
	('Loki', 			'Tyrant', 	50, 	0x9396E6, 	Personality.CHEERFUL.name, 		GemList.AMETHYST.name, 		'https://static.wikia.nocookie.net/megamitensei/images/d/d7/Loki.GIF'),
	('Loki (Paradox)', 	'Vile', 	60, 	0x9396E6, 	Personality.CHEERFUL.name, 		GemList.AMETHYST.name, 		'https://static.wikia.nocookie.net/megamitensei/images/f/f2/Loki4.GIF'),
]

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
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
			gem TEXT,
			image_url TEXT
		)
	''')

	# Insert demon data.
	cursor.executemany('''
		INSERT INTO demons (name, race, rank, colour, personality, gem, image_url) 
		VALUES (?, ?, ?, ?, ?, ?, ?)
	''', demon_data)