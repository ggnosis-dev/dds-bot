import discord
import random

from abc import ABC, abstractmethod
from cogs.demons import DemonQueries, DemonData
from discord.ext import commands
from helpers import checks, currency_queries, players
from shared_enums import Emotes, Personality, ResponseType


dedicated_channel = 1486290442877407333

DIALOGUE_OPTIONS = [
	{"label": "Cheerful", "response": { Personality.CHEERFUL: ResponseType.GOOD, Personality.SHY: ResponseType.NEUTRAL, Personality.AGGRESSIVE: ResponseType.BAD }},
	{"label": "Shy", "response": { Personality.CHEERFUL: ResponseType.NEUTRAL, Personality.SHY: ResponseType.GOOD, Personality.AGGRESSIVE: ResponseType.BAD }},
	{"label": "Aggressive", "response": { Personality.CHEERFUL: ResponseType.BAD, Personality.SHY: ResponseType.BAD, Personality.AGGRESSIVE: ResponseType.GOOD }},
]

class Encounters(commands.Cog):
	'''Cog handles standard type demon encounters. Encounter is represented as a layout view with options as buttons.'''
	def __init__(self, bot: commands.Bot):
		'''
		Init for the Encounters cog.
		
		Args:
			bot (commands.Bot): The bot instance to access other cogs and send messages.
		'''
		self.bot = bot
		self.demon_db = DemonQueries()
		self.player_db = players.Players()


	@checks.is_developer()
	@checks.has_profile()
	@commands.command(name = 'encounter', aliases = ['e'], help = "Start a test encounter with a random demon.")
	async def test_encounter_command(self, ctx) -> None:
		'''Command to start a test encounter with a random demon.'''
		await self._start_encounter(ctx.channel)


	@commands.command(name = 'start', help = "Sets up the player to start playing.")
	async def start_tutorial_command(self, ctx) -> None:
		'''Stores new player data into the DB and begins a forced encounter with a Pixie that acts as a tutorial.'''
		if await self.player_db.setup_player(ctx):
			send_to_channel = self.bot.get_channel(dedicated_channel) or ctx.channel
			
			if not isinstance(send_to_channel, discord.TextChannel):
				raise RuntimeError("ERROR: Could not find the channel to send the encounter to.")

			await ctx.send("Starting your first encounter...")
			demon = self.demon_db.get_demon_by_id(1)

			if demon is None:
				raise RuntimeError("ERROR: Demon at ID 1 not found in the database.")

			view = EncounterViewInitial(demon, self, user_exclusive_to = ctx.author, tutorial = True)
			await send_to_channel.send(view = view)


	async def _start_encounter(self, send_to_channel: discord.TextChannel) -> None:
		'''
		Starts an encounter by selecting a demon and creating a layout view. It will send the encounter to the 
		specified channel, which can be configured to a dedicated channel if necessary.

		Args:
			send_to_channel (discord.TextChannel): Channel to send the encounter to.
		'''
		demon = self.demon_db.get_random_demon()
		count = random.randint(1, 3)
		view = EncounterViewInitial(demon, self, count)
		await send_to_channel.send(view = view)


	async def join_player_party(
		self, 
		player: discord.User | discord.Member, 
		server: discord.Guild | None, 
		demon: DemonData
	) -> bool:
		'''
		Sends a request to the Players cog to add a demon to the player's party and comp. 

		Args: 
			player (discord.User | discord.Member): Player to add the demon for.
			server (discord.Guild | None): Server the player is in.
			demon (DemonData): Demon's data to be added.
		Returns:
			bool: True if the demon was NEWLY ADDED to the compendium, False if it was just added to the party.
		'''
		server_id = server.id if server else None

		if server_id is None:
			raise RuntimeError("ERROR: Server ID is None.")

		currency_queries.update_mag(player.id, server_id, 100)

		new_entry = await self.player_db.add_demon_to_compendium(player.id, server_id, demon.id, demon.rank)
		await self.player_db.set_demon_in_party(player.id, server_id, demon.id)
		return new_entry


class EncounterViewTemplate(discord.ui.LayoutView, ABC):
	'''Base layout view for encounters. Has shared logic for handling dialogue options and interactions.'''
	def __init__(
		self, 
		demon: DemonData,
		encounters_cog: Encounters,
		consecutive_bad_interactions: int = 0,
		message: discord.Message | None = None,
		tutorial: bool = False
	) -> None:
		'''
		Init for the base encounter view.

		Args:
			demon (DemonData): The encounter's demon information.
			encounters_cog (Encounters): The Encounters cog instance to call functions on.
			consecutive_bad_interactions (int, optional): The number of consecutive bad interactions that have occurred in the encounter so far. Defaults to 0.
			message (discord.Message | None, optional): The message the encounter is associated with, used for editing the view on followups and when encounter finishes. Defaults to None.
			tutorial (bool, optional): Whether this encounter is a tutorial encounter, which has different flee logic. Defaults to False.
		'''
		super().__init__()

		self.demon = demon
		self.encounters_cog = encounters_cog
		self.consecutive_bad_interactions = consecutive_bad_interactions
		self.message = message
		self.tutorial = tutorial
		self.status_display: discord.ui.TextDisplay | None = None
		self.parent_view: EncounterViewTemplate | None = None


	@abstractmethod
	def _build_layout(self, message: str, dialogue_options: list[dict]) -> None:
		'''Override in subclasses to build the layout of the encounter.'''
		pass


	@property
	def _root_view(self) -> EncounterViewTemplate:
		'''Helper property to get the parent view that has the icon count and status display.'''
		parent = self.parent_view or self
		return parent


	def _update_icon_count(self) -> None:
		'''Override in initial encounter views.'''
		pass
	

	def _disable_buttons(self) -> None:
		'''Helper function to disable all buttons in a view.'''
		for section in self._option_sections:
			section.accessory.disabled = True


	def _build_option_buttons(self, container: discord.ui.Container, dialogue_options: list[dict]) -> None:
		'''
		Build any dialogue option buttons into the container.

		Args:
			container (discord.ui.Container): Container to add the buttons to.
			dialogue_options (list[dict]): List of dialogue options, where key is the button 'label' and value is 'response' that maps Personality types to ResponseType.
		'''
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
		'''
		Factory to create a dialogue button's callback for any given option index. Each button will remember
		the option index it corresponds to so we can determine the outcome of the encounter based on personality and response.

		Args:
			option_index (int): Index of the dialogue option to create the callback for.
		Returns:
			Callable: The callback function for the dialogue option.
		'''
		async def callback(interaction: discord.Interaction) -> None:
			'''
			Callback function for when a dialogue option button is pressed. Determines the outcome of encounter 
			based on the demon's personality and the option's response type, then updates accordingly.

			Args:
				interaction (discord.Interaction): The Discord interaction object from the button press.
			'''
			option = self.dialogue_options[option_index]
			outcome = option['response'][self.demon.personality_type]

			match outcome:
				case ResponseType.GOOD:
					# Send ephemeral message that demon will join, edit the footer.
					await self._encounter_successful(interaction)
				case ResponseType.BAD:
					# Send followup message with new options.
					bad_count = self.consecutive_bad_interactions + 1

					if bad_count >= 2 and self.tutorial == False:
						await self._encounter_flee(interaction)
					else:
						await self._encounter_followup(interaction)
				case _:
					await self._encounter_followup(interaction)
		
		return callback
	

	async def _encounter_successful(self, interaction: discord.Interaction) -> None:
		'''
		Handler for when an encounter is successful. Adds to party and comp, then sends an ephemeral 
		message confirming the demon has joined.

		Args:
			interaction (discord.Interaction): The Discord interaction object from the button press.
		'''
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


	async def _encounter_flee(self, interaction: discord.Interaction) -> None:
		'''Handler for when encounter flees. Sends an ephemeral message that the demon has fled and updates the status.

		Args:
			interaction (discord.Interaction): The Discord interaction object from the button press.
		'''
		await self._handle_demon_interacted(interaction, f"{self.demon.race} {self.demon.name} has fled from {interaction.user.mention}...")


	async def _encounter_followup(self, interaction: discord.Interaction) -> None:
		'''
		Handler for when encounter needs a followup. This happens on neutral responses, and on bad responses that 
		haven't hit the flee threshold. Creates a new ephemeral message with new dialogue options.

		Args:
			interaction (discord.Interaction): The Discord interaction object from the button press.
		'''
		# For followup encounters, keep track of the parent view.
		parent_view = self._root_view

		followup_view = EncounterViewFollowup(
			demon = self.demon,
			encounters_cog = self.encounters_cog,
			parent_view = parent_view,
			consecutive_bad = self.consecutive_bad_interactions + 1,
			tutorial = self.tutorial
		)

		# On consecutive followups, we want to make sure buttons will get disabled. First followup we don't want to disable any buttons.
		if self.parent_view is not None:
			# Edit the existing ephemeral message to disable buttons, then send the next one.
			await interaction.response.edit_message(view = self)
			await interaction.followup.send(view = followup_view, ephemeral = True)
		else: 
			await interaction.response.send_message(view = followup_view, ephemeral = True)


	async def _handle_demon_interacted(self, interaction: discord.Interaction, status_message: str) -> None:
		'''
		Handler for when an encounter has finished. Updates the status message and icon count, then edits the original 
		parent view message to reflect the outcome.

		Args:
			interaction (discord.Interaction): The Discord interaction object from the button press.
			status_message (str): The message to display in the status of the parent view after interaction.
		'''
		# For finished encounters, update the parent_view if we've had a followup.
		parent_view = self._root_view
		parent_view._update_icon_count()

		if parent_view.status_display is not None:
			parent_view.status_display.content = parent_view.status_display.content + f"\n-# > *{status_message}*"
		
		# If this is a followup view...
		if parent_view is not self and parent_view.message is not None:
			# Update the original message with the new view that has the updated icon count and status message.
			await parent_view.message.edit(view = parent_view)
			await interaction.response.edit_message(view = self)
			await interaction.followup.send(status_message, ephemeral = True)
		else:
			# For the initial view, edit the message with any changes to icon count and status.
			await interaction.response.edit_message(view = parent_view)
			await interaction.followup.send(status_message, ephemeral = True)


class EncounterViewInitial(EncounterViewTemplate):
	'''
	Initial encounter view that will spawn with the demon. Has an icon display that represents the number of 
	interactions left and a status display that updates with each successful interaction. Once the icon count hits 0, 
	the buttons are disabled.
	'''
	def __init__(
		self, 
		demon: DemonData, 
		encounters_cog: Encounters, 
		count: int = 1, 
		user_exclusive_to: discord.User | None = None,
		tutorial = False
	) -> None:
		'''
		Init for the initial encounter view.

		Args:
			demon (DemonData): The encounter's demon information.
			encounters_cog (Encounters): The Encounters cog instance to call functions on.
			count (int, optional): The number of interactions before encounter ends. Defaults to 1.
			user_exclusive_to (discord.User | None, optional): If set, only this user can interact with the encounter. Defaults to None.
			tutorial (bool, optional): If set to True, the encounter can't be failed. Defaults to False.
		'''
		super().__init__(demon, encounters_cog, tutorial = tutorial)

		self.count = count
		self.user_exclusive_to = user_exclusive_to
		self.parent_view = self

		# Set to keep track of the users who have interacted with the encounter to prevent multiple interactions.
		self.interacted_users: set[int] = set()
		self.icon_display = discord.ui.TextDisplay((Emotes.ICON.value + " ") * self.count)

		self._build_layout("Hey, what's going on?", DIALOGUE_OPTIONS)


	def _build_layout(self, message: str, dialogue_options: list[dict]) -> None:
		'''
		Function to build the view layout for the initial encounter. Creates icons, status display, and dialogue option buttons.

		Args:
			message (str): The initial message to display from the demon.
			dialogue_options (list[dict]): List of dialogue options, where key is the button 'label' and value is 'response' that maps Personality types to ResponseType.
		'''
		ui = discord.ui
		container = ui.Container(accent_color = self.demon.colour)
		
		container.add_item(self.icon_display)
		container.add_item(ui.TextDisplay(f"### {self.demon.race} {self.demon.name}!\n-# {message}\n"))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)

		container.add_item(ui.MediaGallery().add_item(media = self.demon.image_url))

		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.small))
		self.status_display = ui.TextDisplay(f"-# *What will you do?*")
		container.add_item(self.status_display)

		self.add_item(container)


	def _make_dialogue_callback(self, option_index: int):
		'''
		Extension of _make_dialogue_callback from the base view and adds a layer of logic to handle user exclusivity and multiple interactions. 

		Args:
			option_index (int): Index of the dialogue option to create the callback for.
		Returns:
			Callable: Callback function for the dialogue option logic for user exclusivity and multiple interactions.
		'''
		# Explicitly build the callback, not just use super().
		base_callback = EncounterViewTemplate._make_dialogue_callback(self, option_index)
	
		async def callback(interaction: discord.Interaction) -> None:
			'''
			Adds layer of logic to check if encounter is exclusive to a user and to ensure once a user interacts with the encounter, they are 
			added to a set and prevented from interacting again.

			Args:
				interaction (discord.Interaction): The Discord interaction object from the button press.
			'''
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
	

	def _update_icon_count(self):
		'''Updates icon count display by decrementing count and updating the content. If count hits 0, disable the buttons to end the encounter.'''
		self.count -= 1

		# This check is necessary as content being empty causes an exception.
		if self.count > 0:
			self.icon_display.content = (Emotes.ICON.value + " ") * self.count
		else:
			self.icon_display.content = Emotes.BLANK.value
			self._disable_buttons()


class EncounterViewFollowup(EncounterViewTemplate):
	'''
	Followup encounter view that spawns on either a neutral or bad response. Similar layout to the initial but without 
	icons, media gallery and status display footer. Does not need to know who interaction is exclusive to as it uses ephemeral messages.
	'''
	def __init__(
		self, 
		demon: DemonData, 
		encounters_cog: Encounters, 
		parent_view: EncounterViewTemplate, 
		consecutive_bad: int = 0,
		tutorial = False
	):
		'''
		Init for the followup encounter view.

		Args:
			demon (DemonData): The encounter's demon information.
			encounters_cog (Encounters): The Encounters cog instance to call functions on.
			parent_view (EncounterViewTemplate): Parent view that spawned this followup, used for updating status and icon count on the original message.
			consecutive_bad (int, optional): Number of consecutive bad interactions that have occurred in the encounter so far, used for flee logic. Defaults to 0.
			tutorial (bool, optional): Whether this encounter is a tutorial encounter, which prevents encounter from fleeing. Defaults to False.
		'''
		super().__init__(demon, encounters_cog, consecutive_bad, tutorial = tutorial)

		self.parent_view = parent_view
		self.interacted = False

		self._build_layout("seems disinterested...", DIALOGUE_OPTIONS)


	def _build_layout(self, message: str, dialogue_options: list[dict]) -> None:
		'''
		Function to build the view layout for the followup encounter.

		Args:
			message (str): The initial message to display from the demon.
			dialogue_options (list[dict]): List of dialogue options, where key is the button 'label' and value is 'response' that maps Personality types to ResponseType.
		'''
		ui = discord.ui
		container = ui.Container(accent_color = self.demon.colour)

		container.add_item(ui.TextDisplay(f'## {self.demon.race} {self.demon.name} {message}'))
		container.add_item(ui.Separator(spacing = discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)
		self.add_item(container)


	def _make_dialogue_callback(self, option_index: int):
		'''
		Extension of _make_dialogue_callback from the base view and adds a layer of logic to handle disabling buttons after an interaction.
		
		Args:
			option_index (int): Index of the dialogue option to create the callback for.
		'''
		base_callback = EncounterViewTemplate._make_dialogue_callback(self, option_index)

		async def callback(interaction: discord.Interaction) -> None:
			'''
			Adds a layer of logic to disable buttons after an interaction so that the user can only interact with the followup once, 
			preventing multiple interactions.

			Args:
				interaction (discord.Interaction): The Discord interaction object from the button press.
			'''
			if self.interacted:
				await interaction.response.defer()
				return
			
			self.interacted = True
			self._disable_buttons()
			await base_callback(interaction)
		
		return callback


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(Encounters(bot))
