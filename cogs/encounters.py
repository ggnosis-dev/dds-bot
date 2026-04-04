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


class BaseEncounterView(discord.ui.LayoutView):
	def __init__(
		self, 
		demon: DemonData,
		encounters_cog: Encounters,
		consecutive_bad: int = 0,
		message: discord.Message | None = None,
		tutorial: bool = False
	):
		super().__init__()

		self.demon = demon
		self.encounters_cog = encounters_cog
		self.consecutive_bad_interactions = consecutive_bad
		self.message = message
		self.tutorial = tutorial
		self.status_display: discord.ui.TextDisplay | None = None
	

	def update_icon_count(self):
		"""Override in subclasses that have icon displays."""
		pass


	def _build_layout(self, message: str, dialogue_options: list[dict]):
		"""Override in subclasses to build the layout of the encounter."""
		pass


	def _disable_buttons(self):
		for section in self._option_sections:
			section.accessory.disabled = True


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
				case ResponseType.BAD:
					# Send followup message with new options.
					bad_count = self.consecutive_bad_interactions + 1

					print(f"INFO: Bad outcome for {interaction.user.name}, consecutive bad interactions: {bad_count}. Tutorial mode: {self.tutorial}")
					if bad_count >= 2 and self.tutorial == False:
						await self._encounter_flee(interaction)
					else:
						await self._encounter_followup(interaction)
				case _:
					print(f"INFO: Neutral outcome for {interaction.user.name}, no changes to encounter state.")
					await self._encounter_followup(interaction)
		
		return callback
	

	async def _encounter_successful(self, interaction: discord.Interaction):
		user = interaction.user
		d_name = self.demon.name
		d_race = self.demon.race

		new_entry = await self.encounters_cog.join_player_party(
			user, interaction.guild, self.demon
		)	

		if new_entry:
			status = f"{d_race} {d_name} was registered to {user.mention}'s compendium!"
		else:
			status = f"{d_race} {d_name} has joined {user.mention}'s party!"
		
		await self._handle_demon_interacted(interaction, status)


	async def _encounter_flee(self, interaction: discord.Interaction):
		await self._handle_demon_interacted(interaction, f"{self.demon.race} {self.demon.name} has fled from {interaction.user.mention}...")


	async def _encounter_followup(self, interaction: discord.Interaction):
		# For followup encounters, keep track of the parent view.
		parent_view = self.parent_view if isinstance(self, FollowupEncounterView) else self

		followup_emph_view = FollowupEncounterView(
			demon = self.demon,
			encounters_cog = self.encounters_cog,
			parent_view = parent_view,
			consecutive_bad = self.consecutive_bad_interactions + 1,
			tutorial = self.tutorial
		)

		# On consecutive followups, we want to make sure buttons will get disabled. First followup we don't want to disable any buttons.
		if isinstance(self, FollowupEncounterView):
			# Edit the existing ephemeral message to disable buttons, then send the next one.
			await interaction.response.edit_message(view = self)
			await interaction.followup.send(view = followup_emph_view, ephemeral = True)
		else: 
			await interaction.response.send_message(view = followup_emph_view, ephemeral = True)


	async def _handle_demon_interacted(self, interaction: discord.Interaction, status_message: str):
		# For finished encounters, update the parent_view if we've had a followup.
		target_view = self.parent_view if isinstance(self, FollowupEncounterView) else self
		target_view.update_icon_count()

		if target_view.status_display is not None:
			target_view.status_display.content = target_view.status_display.content + f"\n-# > *{status_message}*"
		
		# If this is a followup view...
		if isinstance(self, FollowupEncounterView) and target_view.message is not None:
			# Update the original message with the new view that has the updated icon count and status message.
			await target_view.message.edit(view = target_view)
			await interaction.response.edit_message(view = self)
			await interaction.followup.send(status_message, ephemeral = True)
		else:
			# For the initial view, edit the message with any changes to icon count and status.
			await interaction.response.edit_message(view = target_view)
			await interaction.response.defer()
			await interaction.followup.send(status_message, ephemeral = True)


class InitialEncounterView(BaseEncounterView):
	def __init__(
		self, 
		demon: DemonData, 
		encounters_cog: Encounters, 
		count: int = 1, 
		user_exclusive_to: discord.User | None = None,
	):
		super().__init__(demon, encounters_cog)

		self.count = count
		self.user_exclusive_to = user_exclusive_to
		self.parent_view = self

		# Set to keep track of the users who have interacted with the encounter to prevent multiple interactions.
		self.interacted_users: set[int] = set()

		self.icon_display = discord.ui.TextDisplay((Emotes.ICON.value + " ") * self.count)
		self._build_layout("Hey, what's going on?", DIALOGUE_OPTIONS)


	def _build_layout(self, message: str, dialogue_options: list[dict]):
		ui = discord.ui
		container = ui.Container(accent_color = self.demon.colour)

		container.add_item(self.icon_display)
		container.add_item(ui.TextDisplay(f"### {self.demon.race} {self.demon.name}!\n-# {message}\n"))
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
	

	def update_icon_count(self):
		self.count -= 1

		# This check is necessary as content being empty causes an exception.
		if self.count > 0:
			self.icon_display.content = (Emotes.ICON.value + " ") * self.count
		else:
			self.icon_display.content = Emotes.BLANK.value
			self._disable_buttons()


class FollowupEncounterView(BaseEncounterView):
	def __init__(
		self, 
		demon: DemonData, 
		encounters_cog: Encounters, 
		parent_view: BaseEncounterView, 
		consecutive_bad: int = 0,
		tutorial = False
	):
		super().__init__(demon, encounters_cog, consecutive_bad, tutorial = tutorial)

		self.parent_view = parent_view
		self.interacted = False

		self._build_layout("seems disinterested...", DIALOGUE_OPTIONS)


	def _build_layout(self, message: str, dialogue_options: list[dict]):
		ui = discord.ui
		container = ui.Container(accent_color = self.demon.colour)

		container.add_item(ui.TextDisplay(f'## {self.demon.race} {self.demon.name} {message}'))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)
		self.add_item(container)


	def _make_dialogue_callback(self, option_index: int):
		base_callback = BaseEncounterView._make_dialogue_callback(self, option_index)

		async def callback(interaction: discord.Interaction):
			if self.interacted:
				await interaction.response.defer()
				return
			
			self.interacted = True
			self._disable_buttons()
			await base_callback(interaction)
		
		return callback


class Encounters(commands.Cog):
	'''
	Cog handles random encounters. It currently listens to messages and after a number of them,
	will trigger an encounter. The encounter is represented as an embed with options as buttons.
	'''
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		# self.message_counter = 2
		# self.encounter_threshold = random.randint(1, 2)

	
	async def start_encounter(self, send_to_channel: discord.TextChannel):
		'''
		Starts an encounter by selecting a demon and creating a layout view.
		It will send the encounter to the specified channel, which can be configured to a dedicated 
		channel if necessary.
		'''
		demon_cog 	= self.bot.get_cog('Demon')
		demon 		= demon_cog.get_random_demon()	# type: ignore
		count 		= random.randint(1, 3)
		view		= InitialEncounterView(demon, self, count)
		message		= await send_to_channel.send(view = view)

		view.message = message


	async def start_tutorial_encounter(self, send_to_channel: discord.TextChannel, user: discord.User):
		'''
		Starts a forced encounter with a Pixie (ID 1) that acts as a tutorial.
		'''
		demon_cog 	= self.bot.get_cog('Demon')
		demon 		= demon_cog.get_demon_by_id(1)	# type: ignore
		view		= InitialEncounterView(demon, self)
		message		= await send_to_channel.send(view = view)

		view.user_exclusive_to = user
		view.message = message
		view.tutorial = True
		# demon_cog = self.bot.get_cog('Demon')
		# demon = demon_cog.get_demon_by_id(1)	# type: ignore

		# if demon is None : return

		# happiness_val = 80
		# dialogue_options = DIALOGUE_OPTIONS
		# count = 1

		# embed 	= EncounterEmbed(demon, f"Hey {user.mention}, what's going on?", dialogue_options, count)
		# view 	= EncounterView(demon, dialogue_options, happiness_val, self, count, user)

		# view.create_default_button_view(True)
		# message = await send_to_channel.send(embed = embed, view = view)
		# view.message = message
		pass


	async def join_player_party(self, player: discord.User | discord.Member, server: discord.Guild | None, demon: DemonData) -> bool:
		'''
		Function for when a demon JOINS the player's party from an encounter. If it is a new demon, it will be added to the compendium and return True.
		If it exists in it already, join the party at the default rank and return with False.
		'''
		players_cog = self.bot.get_cog('Players')
		new_entry = await players_cog.add_demon_to_compendium(player.id, server.id, demon.id, demon.rank)	# type: ignore
		await players_cog.set_demon_in_party(player.id, server.id, demon.id)								# type: ignore
		return new_entry
	

	# @commands.Cog.listener()
	# async def on_message(self, message: discord.Message):
	# 	if message.author == self.bot.user:
	# 		return
		
	# 	self.message_counter += 2

	# 	if self.message_counter >= self.encounter_threshold:

	# 		send_to_channel_id = dedicated_channel if dedicated_channel else message.channel.id
	# 		channel = self.bot.get_channel(send_to_channel_id)

	# 		if not isinstance(channel, discord.TextChannel):
	# 			return

	# 		await self.start_encounter(channel)

	# 		# Reset message counter.
	# 		self.message_counter = 0
	# 		self.encounter_threshold = random.randint(1, 2)


# Add the cog to the bot.
async def setup(bot: commands.Bot):
	await bot.add_cog(Encounters(bot))
