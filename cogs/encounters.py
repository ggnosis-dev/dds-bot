import discord
import random

from cogs.demons import DemonData
from discord.ext import commands
from shared_enums import Emotes, Personality, ResponseType

dedicated_channel = 1486290442877407333

DIALOGUE_OPTIONS = [
	{"label": "Cheerful", "response": { Personality.CHEERFUL: ResponseType.GOOD, Personality.SHY: ResponseType.NEUTRAL, Personality.AGGRESSIVE: ResponseType.BAD }},
	{"label": "Shy", "response": { Personality.CHEERFUL: ResponseType.NEUTRAL, Personality.SHY: ResponseType.GOOD, Personality.AGGRESSIVE: ResponseType.BAD }},
	{"label": "Aggressive", "response": { Personality.CHEERFUL: ResponseType.BAD, Personality.SHY: ResponseType.BAD, Personality.AGGRESSIVE: ResponseType.GOOD }},
]


class EncounterEmbed(discord.Embed):
	def __init__(self, demon: DemonData, intro_message: str, dialogue_options: list[dict], count: int = 0):
		super().__init__(
			title = (Emotes.ICON.value + " ") * count,
			color = demon.colour
		)

		self.add_field(
			name 	= f"{demon.race} {demon.name}!", 
			value 	= f'{intro_message}\n{Emotes.BLANK.value}', 
			inline 	= False
		)

		# Cycle through dialogue options and add them as fields to the embed.
		for i, option in enumerate(dialogue_options):
			self.add_field(name = f"Option {i + 1}", value = option['label'], inline = True)

		self.set_image(url = demon.image_url)
		# self.set_thumbnail(url = demon.image_url)
		self.set_footer(text = "What will you do?")


class EncounterView(discord.ui.View):
	'''
	A view will persist for the duration of the encounter. It holds the state of the encounter. It is necessary to create 
	interactive components like buttons. 

	Any edits to the embed after the initial message is sent is done here. We need a reference to the message first, hence why
	the view is responsible for updating and editing the embed.
	'''
	def __init__(
		self, 
		demon				: DemonData, 
		dialogue_options	: list[dict], 
		happiness_val		: int,
		encounters_cog		: Encounters,
		count				: int = 1,
		user_exclusive_to	: discord.User | None = None,
	):
		# Initialize the view with a timeout of 60 seconds.
		super().__init__(timeout = 60)

		self.demon 				= demon
		self.dialogue_options 	= dialogue_options
		self.happiness_val 		= happiness_val
		self.count 				= count
		self.encounters_cog 	= encounters_cog
		self.user_exclusive_to 	= user_exclusive_to

		# Reference to the message which will let us edit the embed later on if necessary.
		self.message: discord.Message | None = None

		# Set to keep track of the users who have interacted with the encounter to prevent multiple interactions.
		self.interacted_users: set[int] = set()

		# Keep track of user and their current happiness value.
		self.interacting_users: dict[int, int] = {}


	async def update_icon_count(self):
		if self.message is None : return

		self.count -= 1
		embed = self.message.embeds[0]
		embed.title = (Emotes.ICON.value + " ") * self.count
		await self.message.edit(embed = embed)

		if self.count <= 0:
			# Remove buttons from view if it's done.
			await self.message.edit(embed = embed, view = None)


	def update_footer_message(self, message: str, icon_url: str | None = None):
		if self.message is None : return

		embed = self.message.embeds[0]
		existing_footer = embed.footer.text or ""
		new_footer = f"{existing_footer}\n{message}"

		embed.set_footer(text = new_footer, icon_url = icon_url)


	def create_default_button_view(self, tutorial: bool = False):
		button_emotes = [Emotes.ONE, Emotes.TWO, Emotes.THREE]

		for i, e in enumerate(button_emotes):
			# Add a button for each option.
			button = discord.ui.Button(emoji = e.value, style = discord.ButtonStyle.grey)

			if tutorial:
				button.callback = self.tutorial_button_callback()
			else:
				button.callback = self.button_callback(e.value, self.dialogue_options[i]['response'])
			self.add_item(button)


	def button_callback(self, label: str, response: dict):
		async def callback(interaction: discord.Interaction):
			# Check if user has already interacted.
			if interaction.user.id in self.interacted_users : return

			if interaction.user.id not in self.interacting_users:
				# Set initial happiness for user if they haven't interacted before.
				self.interacting_users[interaction.user.id] = self.happiness_val

			self.interacting_users[interaction.user.id] += response[self.demon.personality_type]

			await interaction.response.send_message(
				f"You chose {label.lower()}\n"
				f"{self.demon.name}'s happiness is now {self.interacting_users[interaction.user.id]}!", 
				ephemeral=True, 
			)

			# TODO: Update this so it's reusable and nicer.
			if self.interacting_users[interaction.user.id] >= 80:
				await self.encounters_cog.join_player_party(interaction.user, interaction.guild, self.demon)
				await self.update_icon_count()
				self.interacted_users.add(interaction.user.id)
			elif self.interacting_users[interaction.user.id] <= 20:
				# Edit the embed to say that the demon has left.
				d_name = self.demon.name
				d_race = self.demon.race
				icon_url = interaction.user.avatar.url if interaction.user.avatar else None
				user_name = interaction.user.name

				self.update_footer_message(f"{d_race} {d_name} has fled from {user_name}!", icon_url)
				await self.update_icon_count()
				self.interacted_users.add(interaction.user.id)

		return callback
	

	def tutorial_button_callback(self):
		async def callback(interaction: discord.Interaction):
			# If user isn't the one who the encounter is for, exit early.
			if interaction.user != self.user_exclusive_to : return
			
			await interaction.response.send_message(
				f"You're interesting, Mister! I think I'll stick around...", 
				ephemeral=True, 
			)

			# Add the demon to the player's party.
			await self.encounters_cog.join_player_party(interaction.user, interaction.guild, self.demon)
			await self.update_icon_count()
		return callback


class BaseEncounterView(discord.ui.LayoutView):
	# row = discord.ui.ActionRow()

	def __init__(
		self, 
		demon: DemonData,
		encounters_cog: Encounters,
	):
		super().__init__()

		self.demon = demon
		self.encounters_cog = encounters_cog

		# Reference to the message which will let us edit the embed later on if necessary.
		self.message: discord.Message | None = None

		# Set to keep track of the users who have interacted with the encounter to prevent multiple interactions.
		self.interacted_users: set[int] = set()

		# Keep track of user and their current happiness value.
		self.interacting_users: dict[int, int] = {}

		self.consecutive_bad_interactions: dict[int, int] = {}

		self.status_display: discord.ui.TextDisplay | None = None
	

	def _build_option_buttons(self, container: discord.ui.Container, dialogue_options: list[dict]):
		# Store dialogue options in the view to access them in the callbacks.
		self.dialogue_options = dialogue_options
		self._option_sections = []
		button_emotes = [Emotes.ONE, Emotes.TWO, Emotes.THREE]

		for i, option in enumerate(dialogue_options):
			button = discord.ui.Button(
				emoji = button_emotes[i].value,
				style = discord.ButtonStyle.grey,
			)
			button.callback = self._make_dialogue_callback(i)

			new_section = discord.ui.Section(accessory = button)
			new_section.add_item(discord.ui.TextDisplay(f"Option {i + 1}: {option['label']}"))

			container.add_item(new_section)
			self._option_sections.append(new_section)


	def _make_dialogue_callback(self, option_index: int):
		async def callback(interaction: discord.Interaction):
			
			option = self.dialogue_options[option_index]
			outcome = option['response'][self.demon.personality_type]

			match outcome:
				case ResponseType.GOOD:

					# Send ephemeral message that demon will join, edit the footer.
					await self._encounter_successful(interaction)
					pass
				case ResponseType.BAD:
					pass
				case ResponseType.NEUTRAL, _:
					pass
			
		return callback
	

	async def _encounter_successful(self, interaction: discord.Interaction):
		user = interaction.user
		d_name = self.demon.name
		d_race = self.demon.race

		new_entry = await self.encounters_cog.join_player_party(
			user, interaction.guild, self.demon
		)	

		if new_entry:
			status = f"{d_race} {d_name} was registered to {user.name}'s compendium!"
		else:
			status = f"{d_race} {d_name} has joined {user.name}'s party!"
		
		await self._handle_demon_interacted(interaction, status)


	async def _encounter_followup(self, interaction: discord.Interaction):
		user = interaction.user
		d_name = self.demon.name
		d_race = self.demon.race

		await interaction.followup.send(f"Try again {d_race} {d_name}!", ephemeral=True)


	async def _handle_demon_interacted(self, interaction: discord.Interaction, status_message: str):
		# - Send a ephemeral message to the user.
		# - Add a line to the container's status display with outcome.
		# - Add the user to the set of interacted users to prevent multiple interactions.
		# - Add demon to player's party
		if self.status_display is not None:
			self.status_display.content = self.status_display.content + f"\n-# *{status_message}*"
		await interaction.response.edit_message(view = self)
		await interaction.followup.send(status_message, ephemeral=True)


class InitialEncounterView(BaseEncounterView):
	def __init__(self, demon: DemonData, encounters_cog: Encounters, count: int = 1, user_exclusive_to: discord.User | None = None):
		super().__init__(demon, encounters_cog)

		self.count = count
		self.user_exclusive_to = user_exclusive_to
		self.interacted_users: set[int] = set()

		self._build_layout("Hey, what's going on?", DIALOGUE_OPTIONS)


	def _build_layout(self, intro_message: str, dialogue_options: list[dict]):
		ui = discord.ui
		container = ui.Container(accent_color = self.demon.colour)

		container.add_item(ui.TextDisplay((Emotes.ICON.value + " ") * self.count))
		container.add_item(ui.TextDisplay(f"### {self.demon.race} {self.demon.name}!\n-# {intro_message}\n"))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)

		container.add_item(ui.MediaGallery().add_item(media=self.demon.image_url))

		self.status_display = ui.TextDisplay(f"-# *What will you do?*")
		container.add_item(self.status_display)

		self.add_item(container)

	def _make_dialogue_callback(self, option_index: int):
		# Explicitly build the callback, not just use super().
		base_callback = BaseEncounterView._make_dialogue_callback(self, option_index)
	
		async def callback(interaction: discord.Interaction):
			user = interaction.user

			# Check if user has already interacted.
			if user.id in self.interacted_users: 
				await interaction.response.defer()
				return
			
			# If user isn't the one who the encounter is for (when option exists), exit early.
			if self.user_exclusive_to and user != self.user_exclusive_to:
				await interaction.response.defer()
				return
			
			# We only want the user to be able to interact once with the box, 
			# if it's a multi-option encounter, an ephemeral message will be sent next.
			self.interacted_users.add(user.id)

			await base_callback(interaction)

		return callback



class Encounters(commands.Cog):
	'''
	Cog handles random encounters. It currently listens to messages and after a number of them,
	will trigger an encounter. The encounter is represented as an embed with options as buttons.
	'''
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.message_counter = 2
		self.encounter_threshold = random.randint(1, 2)

	
	async def start_encounter(self, send_to_channel: discord.TextChannel):
		'''
		Starts an encounter by selecting a demon and organising the embed and view.
		It will send the encounter to the specified channel, which can be configured to a dedicated 
		channel if necessary.
		'''
		demon_cog = self.bot.get_cog('Demon')
		demon = demon_cog.get_random_demon()	# type: ignore

		if demon is None : return

		dialogue_options = DIALOGUE_OPTIONS
		count = random.randint(1, 3)

		# embed 	= EncounterEmbed(demon, "Hey, what's going on?", dialogue_options, count)
		# view 	= EncounterView(demon, dialogue_options, happiness_val, self, count)
		view = InitialEncounterView(demon, self, count)

		# view.create_default_button_view()
		try: 
			await send_to_channel.send(view=view)
		except Exception as e:
			print(f"Error sending encounter message: {e}")
			return
		# view.message = message


	async def start_tutorial_encounter(self, send_to_channel: discord.TextChannel, user: discord.User):
		'''
		Starts a forced encounter with a specific demon.
		'''
		demon_cog = self.bot.get_cog('Demon')
		demon = demon_cog.get_demon_by_id(1)	# type: ignore

		if demon is None : return

		happiness_val = 80
		dialogue_options = DIALOGUE_OPTIONS
		count = 1

		embed 	= EncounterEmbed(demon, f"Hey {user.mention}, what's going on?", dialogue_options, count)
		view 	= EncounterView(demon, dialogue_options, happiness_val, self, count, user)

		view.create_default_button_view(True)
		message = await send_to_channel.send(embed = embed, view = view)
		view.message = message


	async def join_player_party(self, player: discord.User | discord.Member, server: discord.Guild | None, demon: DemonData) -> bool:
		'''
		Function for when a demon JOINS the player's party from an encounter. If it is a new demon, it will be added to the compendium and return True.
		If it exists in it already, join the party at the default rank and return with False.
		'''
		players_cog = self.bot.get_cog('Players')
		new_entry = await players_cog.add_demon_to_compendium(player.id, server.id, demon.id, demon.rank)	# type: ignore
		await players_cog.set_demon_in_party(player.id, server.id, demon.id)								# type: ignore
		return new_entry
	

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		if message.author == self.bot.user:
			return
		
		self.message_counter += 2

		if self.message_counter >= self.encounter_threshold:

			send_to_channel_id = dedicated_channel if dedicated_channel else message.channel.id
			channel = self.bot.get_channel(send_to_channel_id)

			if not isinstance(channel, discord.TextChannel):
				return

			await self.start_encounter(channel)

			# Reset message counter.
			self.message_counter = 0
			self.encounter_threshold = random.randint(1, 2)


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Encounters(bot))
