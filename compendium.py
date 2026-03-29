import sqlite3

demon_data = [
	('Pixie', 		'Fairy', 	5, 		0xE93700,	'CHEERFUL', 	'https://static.wikia.nocookie.net/megamitensei/images/b/b8/Pixie.GIF'),
	('Jack Frost',	'Fairy',	10, 	0x2A58CC, 	'CHEERFUL', 	'https://static.wikia.nocookie.net/megamitensei/images/a/ab/Jack_Frost.GIF'),
	('Harpy', 		'Fairy', 	15, 	0x9396E6, 	'AGGRESSIVE', 	'https://static.wikia.nocookie.net/megamitensei/images/e/ee/Harpy2.GIF')
]

conn = sqlite3.connect('compendium.db')
cursor = conn.cursor()

# Delete existing demon table.
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

conn.commit()
conn.close()