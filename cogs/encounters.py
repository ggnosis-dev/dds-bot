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
	def __init__(self, name, race, pronouns: Pronouns, colour, personality_type: Personality, image_url):
		self.name = name
		self.race = race
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
				name = row['name'],
				race = row['race'],
				pronouns = PRONOUNS[row['pronouns']],
				colour = int(row['colour'], 16),
				personality_type = Personality[row['personality']],
				image_url = row['image_url'],
			)
			demons.append(demon)
	return demons

DEMONS = load_demons("compendium.csv")

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
	def __init__(self, demon: Demon, dialogue_options):
		super().__init__(
			title=f"{EMOTES['icon']}", 
			color=demon.colour
		)

		print(f'Creating encounter embed for {demon.name} with colour {demon.colour}')
		print(f'Encounter dialogue options: {dialogue_options}')

		self.add_field(name=f"{demon.race} {demon.name}!", value=f"Hey, what's going on?\n{EMOTES['blank']}", inline=False)
		
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
		demon = random.choice(DEMONS)
		happiness_val = 50
		dialogue_options = DIALOGUE_OPTIONS

		embed = EncounterEmbed(demon, dialogue_options)
		view = EncounterView(demon, dialogue_options, happiness_val)

		await self.bot.get_channel(send_to_channel).send(embed=embed, view=view)
		print(f'Sent encounter in channel {send_to_channel}')


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
