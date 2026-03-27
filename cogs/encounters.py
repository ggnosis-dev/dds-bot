import discord
from discord.ext import commands
import random
from enum import Enum
import csv


class Personality(Enum): 
	CHEERFUL = 1
	SHY = 2
	AGGRESSIVE = 3

class Pronouns:
	def __init__(self, subject, object, possessive_adjective, possessive_pronoun, reflexive):
		self.they = subject
		self.them = object
		self.their = possessive_adjective
		self.theirs = possessive_pronoun
		self.themselves = reflexive

PRONOUNS = {
	"he/him"	: Pronouns("he", "him", "his", "his", "himself"),
	"she/her"	: Pronouns("she", "her", "her", "hers", "herself"),
	"they/them"	: Pronouns("they", "them", "their", "theirs", "themselves"),
	"it/its"	: Pronouns("it", "it", "its", "its", "itself")
}

class Demon:
	def __init__(self, id, name, race, rank, pronouns: Pronouns, colour, personality_type: Personality, image_url):
		self.id = id
		self.name = name
		self.race = race
		self.rank = rank
		self.pronouns = pronouns
		self.colour = colour
		self.personality_type = personality_type
		self.image_url = image_url


def load_demons(file_path: str) -> list[Demon]:
	'''
	Loads demons from a CSV file, returning a list of available demons.
	'''
	demons = []
	with open(file_path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			demon = Demon(
				id = int(row['id']),
				name = row['name'],
				race = row['race'],
				rank = int(row['rank']),
				pronouns = PRONOUNS[row['pronouns']],
				colour = int(row['colour'], 16),
				personality_type = Personality[row['personality']],
				image_url = row['image_url'],
			)
			demons.append(demon)
	return demons

# Load demons from the compendium CSV file and create a dictionary for easy access by ID.
DEMONS = {demon.id: demon for demon in load_demons("compendium.csv")}

EMOTES = {
	'1': '\u0031\ufe0f\u20e3',
	'2': '\u0032\ufe0f\u20e3',
	'3': '\u0033\ufe0f\u20e3',
	'icon': '<:__:1486233309078884493>',
	'blank': '<:__:1486236397508628510>',
}

DIALOGUE_OPTIONS = [
	{"label": "Cheerful", "happiness_change": { Personality.CHEERFUL: 25, Personality.SHY: 0, Personality.AGGRESSIVE: -25 }},
	{"label": "Shy", "happiness_change": { Personality.CHEERFUL: 0, Personality.SHY: 25, Personality.AGGRESSIVE: -25 }},
	{"label": "Aggressive", "happiness_change": { Personality.CHEERFUL: -25, Personality.SHY: -25, Personality.AGGRESSIVE: 25 }},
]

dedicated_channel = 1486290442877407333


class EncounterEmbed(discord.Embed):
	def __init__(self, demon: Demon, intro_message, dialogue_options, user_exclusive_to: int | None = None):
		super().__init__(
			title=f"{EMOTES['icon']}", 
			color=demon.colour
		)

		self.add_field(
			name=f"{demon.race} {demon.name}!", 
			value=f'{intro_message}\n{EMOTES['blank']}', 
			inline=False
		)
		
		# Cycle through dialogue options and add them as fields to the embed.
		for i, option in enumerate(dialogue_options):
			self.add_field(name=f"Option {i + 1}", value=option['label'], inline=True)

		self.set_image(url=demon.image_url)
		self.set_thumbnail(url=demon.image_url)
		self.set_footer(text="What will you do?")

		print(f'Created encounter embed for {demon.name}')


class EncounterView(discord.ui.View):
	'''
	A view is necessary to create interactive components like buttons.
	Here, we're creating options for an encounter which should trigger a response when clicked.
	'''
	def __init__(self, demon: Demon, dialogue_options: list[dict], happiness_val: int):
		# Initialize the view with a timeout of 60 seconds.
		super().__init__(timeout=60)
		self.demon = demon
		self.dialogue_options = dialogue_options
		self.happiness_val = happiness_val

		button_emotes = ['1', '2', '3']

		for i, e in enumerate(button_emotes):
			# Add a button for each option.
			button = discord.ui.Button(emoji=EMOTES[e], style=discord.ButtonStyle.grey)

			# Set what happens when button is clicked.
			button.callback = self.button_callback(e, self.dialogue_options[i]['happiness_change'])
			self.add_item(button)

		print('Created encounter view with buttons')
	

	def button_callback(self, label: str, happiness_change: dict):
		'''
		Callback sends a message exclusively to the user who clicked the button, confirming their choice.
		'''
		async def callback(interaction: discord.Interaction):
			self.happiness_val += happiness_change[self.demon.personality_type]
			await interaction.response.send_message(
				f"You chose {label.lower()}\n"
				f"{self.demon.name}'s happiness is now {self.happiness_val}!", 
				ephemeral=True, 
				# view=self
			)
		return callback


class EncounterTutorialView(EncounterView):
	def __init__(
		self, 
		demon: Demon, 
		dialogue_options: list[dict], 
		happiness_val: int,
		user_exclusive_to: discord.User,
		encounters_cog
	):
		super().__init__(demon, dialogue_options, happiness_val)
		self.user_exclusive_to = user_exclusive_to
		self.encounters_cog = encounters_cog


	def button_callback(self, label: str, happiness_change: dict):
		
		async def callback(interaction: discord.Interaction):
			# If user isn't the one who the encounter is for, exit early.
			if interaction.user != self.user_exclusive_to : return
			
			await interaction.response.send_message(
				f"You're interesting, Mister! I think I'll stick around...", 
				ephemeral=True, 
			)

			# Add the demon to the player's party.
			await self.encounters_cog.join_player_party(interaction.user.id, interaction.guild_id, self.demon)
		return callback


class Encounters(commands.Cog):
	'''
	Cog handles random encounters. It currently listens to messages and after a number of them,
	will trigger an encounter. The encounter is represented as an embed with options as buttons.
	'''
	def __init__(self, bot):
		self.bot = bot
		self.message_counter = 2
		self.encounter_threshold = random.randint(1, 2)

	
	async def start_encounter(self, send_to_channel: int):
		'''
		Starts an encounter by selecting a demon and organising the embed and view.
		It will send the encounter to the specified channel, which can be configured to a dedicated 
		channel if necessary.
		'''
		print(f'Starting encounter in channel {send_to_channel}')

		demon = random.choice(list(DEMONS.values()))
		happiness_val = 50
		dialogue_options = DIALOGUE_OPTIONS

		embed 	= EncounterEmbed(demon, "Hey, what's going on?", dialogue_options)
		view 	= EncounterView(demon, dialogue_options, happiness_val)

		await self.bot.get_channel(send_to_channel).send(embed = embed, view = view)
		print(f'Sent encounter in channel {send_to_channel}')


	async def start_tutorial_encounter(self, send_to_channel: int, user):
		'''
		Starts a forced encounter with a specific demon.
		'''
		print(f'Starting tutorial encounter in channel {send_to_channel} for user {user}')
		demon = DEMONS[1]
		happiness_val = 80
		dialogue_options = DIALOGUE_OPTIONS
		print(f'Creating tutorial encounter embed and view for user {user}')

		embed 	= EncounterEmbed(demon, f"Hey {user.mention}, what's going on?", dialogue_options)
		view 	= EncounterTutorialView(demon, dialogue_options, happiness_val, user, self)

		await self.bot.get_channel(send_to_channel).send(embed = embed, view = view)


	async def join_player_party(self, player_id: int, server_id: int, demon: Demon):
		players_cog = self.bot.get_cog('Players')
		await players_cog.add_demon_to_party(player_id, server_id, demon.id, demon.rank)


	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		
		self.message_counter += 2

		if self.message_counter >= self.encounter_threshold:
			send_to_channel: int = dedicated_channel if dedicated_channel != None else message.channel
			await self.start_encounter(send_to_channel)

			# Reset message counter.
			self.message_counter = 0
			self.encounter_threshold = random.randint(1, 2)


# Add the cog to the bot.
async def setup(bot):
	await bot.add_cog(Encounters(bot))
