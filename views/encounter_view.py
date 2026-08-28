import asyncio

from abc import ABC, abstractmethod

import discord

from entities.demon_data import DemonData
from entities.encounter_data import AnswerData, ReactionData
from helpers.encounter_utils import join_player_party
from helpers.format_utils import format_dialogue, format_greeting
from queries import player_demons_queries, talk_queries
from shared_enums import DemonRegistration, Emotes, ResponseType, Unicode
from views.common_view import MessageView

# 5 minute timeout.
ENCOUNTER_TIMEOUT = 5 * 60
BAD_COUNT_INCREMENT = {ResponseType.NEUTRAL: 1, ResponseType.BAD: 2}
FLEE_THRESHOLD = 3


class EncounterViewTemplate(discord.ui.LayoutView, ABC):
	"""
	Base layout view for encounters. Shared logic for handling dialogue options and interactions.
	"""

	def __init__(
		self,
		demon: DemonData,
		summoner_id: int,
		count: int = 1,
		consecutive_bad_interactions: int = 0,
		message: discord.Message | None = None,
		tutorial: bool = False,
	) -> None:
		"""
		Init for the base encounter view.

		Args:
			demon (DemonData): The encounter's demon information.
			consecutive_bad_interactions (int, optional): The number of consecutive bad interactions
				that have occurred in the encounter so far. Defaults to 0.
			message (discord.Message | None, optional): Message the encounter is associated with,
				used for editing the view on followups and when encounter finishes.
			tutorial (bool, optional): Whether this encounter is a tutorial encounter, which has
				different flee logic. Defaults to False.
		"""
		super().__init__(timeout=ENCOUNTER_TIMEOUT)

		self.demon = demon
		self.summoner_id = summoner_id
		self.count = count
		self.consecutive_bad_interactions = consecutive_bad_interactions
		self.message = message
		self.tutorial = tutorial

		self.talk_data = talk_queries.get_talk_dialogue(demon.tone_type.value, demon.personality_type.value)

		self.status_display: discord.ui.TextDisplay | None = None
		self.parent_view: EncounterViewTemplate | None = None

	@abstractmethod
	def _build_layout(self, question: str, dialogue_options: tuple[AnswerData, ...]) -> None:
		"""Override in subclasses to build the layout of the encounter."""
		pass

	@property
	def _root_view(self) -> "EncounterViewTemplate":
		"""Helper property to get the parent view that has the icon count and status display."""
		parent = self.parent_view or self
		return parent

	def _update_icon_count(self) -> None:
		"""Override in initial encounter views."""
		pass

	def _disable_buttons(self) -> None:
		"""Helper function to disable all buttons in a view."""
		for section in self._option_sections:
			section.accessory.disabled = True

	def _build_option_buttons(self, container: discord.ui.Container, answers: tuple[AnswerData, ...]) -> None:
		"""
		Build any dialogue option buttons into the container.

		Args:
		    container (discord.ui.Container): Container to add the buttons to.
		    dialogue_options (list[dict]): List of dialogue options, where key is the button 'label'
		        and value is 'response' that maps Personality types to ResponseType.
		"""
		# Store dialogue options in the view to access them in the callbacks.
		self._option_sections = []
		button_emotes = [Emotes.ONE, Emotes.TWO, Emotes.THREE]

		# Enumerate for label and to filter on the right reaction data.
		for i, option in enumerate(answers, 0):
			button = discord.ui.Button(
				emoji=button_emotes[i].value,
				style=discord.ButtonStyle.grey,
			)

			# Callback should know data about the reaction.
			reaction_data = option.reactions[0]
			button.callback = self._make_dialogue_callback(reaction_data)

			new_section = discord.ui.Section(accessory=button)
			new_section.add_item(discord.ui.TextDisplay(f"{option.label}"))

			container.add_item(new_section)
			self._option_sections.append(new_section)

	def _make_dialogue_callback(self, reaction_data: ReactionData):
		"""
		Factory to create a dialogue button's callback for any given option index. Each button will
		remember the reaction_data it corresponds to so we can determine the outcome of the encounter
		based on personality and response.

		Returns:
		    Callable: The callback function for the dialogue option.
		"""

		async def callback(interaction: discord.Interaction) -> None:
			"""
			Callback function for when a dialogue option button is pressed. Determines the outcome
			of encounter based on the demon's personality and the option's response type, then
			updates accordingly.

			Args:
			    interaction (discord.Interaction): Discord interaction object from the button press.
			"""
			# Get the answer at the given button index.
			r_type = reaction_data.response_type
			r_text = reaction_data.response

			# Check the root's count.
			if self._root_view.count <= 0:
				await interaction.response.defer()
				missed_encounter_view = MessageView(
					"All of the available demons have left...",
					colour=self.demon.design_data.colour,
				)
				await interaction.followup.send(view=missed_encounter_view, ephemeral=True)
				return

			match r_type:
				case ResponseType.GOOD:
					# Send ephemeral message that demon will join, edit the footer.
					await self._encounter_successful(interaction, r_text)
				case ResponseType.NEUTRAL | ResponseType.BAD:
					new_bad_count = self.consecutive_bad_interactions + BAD_COUNT_INCREMENT[r_type]

					if new_bad_count >= FLEE_THRESHOLD and not self.tutorial:
						await self._encounter_flee(interaction, r_text)
					else:
						await self._encounter_followup(interaction, r_text, new_bad_count)

		return callback

	async def _encounter_successful(self, interaction: discord.Interaction, response: str) -> None:
		"""
		Handler for when an encounter is successful. Adds to party and comp, then sends an ephemeral
		message confirming the demon has joined.

		Args:
		    interaction (discord.Interaction): The Discord interaction object from the button press.
		"""
		user = interaction.user
		join_data = await join_player_party(user, interaction.guild, self.demon)

		await asyncio.gather(
			self._handle_demon_interacted(
				interaction,
				response,
				join_data.status_message,
				join_data.extra_response,
			),
			self._update_dupe_level(interaction, self.demon, join_data.dupe_message),
		)

	async def _encounter_flee(self, interaction: discord.Interaction, response: str) -> None:
		"""
		Handler for when encounter flees. Sends an ephemeral message that the demon has fled and
		updates the status.

		Args:
		    interaction (discord.Interaction): The Discord interaction object from the button press.
		"""
		await self._handle_demon_interacted(
			interaction, response, f"> {self.demon.race} {self.demon.name} has fled from {interaction.user.name}..."
		)

	async def _encounter_followup(self, interaction: discord.Interaction, response: str, new_bad_count: int) -> None:
		"""
		Handler for when encounter needs a followup. This happens on neutral and on bad responses that haven't hit the flee
		threshold. Creates a new ephemeral message with new dialogue options.

		Args:
		    interaction (discord.Interaction): The Discord interaction object from the button press.
			response (str): The final outcome message of the previous interaction to send to the player.
		"""

		# For followup encounters, keep track of the parent view.
		parent_view = self._root_view

		followup_view = EncounterViewFollowup(
			self.demon,
			self.summoner_id,
			parent_view,
			response,
			consecutive_bad=new_bad_count,
			tutorial=self.tutorial,
		)

		# On consecutive followups, we want to make sure buttons from the previous ones will get disabled.
		if isinstance(self, EncounterViewFollowup):
			# Edit the existing ephemeral message to disable buttons, then send the next one.
			await interaction.response.edit_message(view=self)
			await interaction.followup.send(view=followup_view, ephemeral=True)
		else:
			# This is the initial view, which we don't want to edit in case someone else interacts with it.
			await interaction.response.send_message(view=followup_view, ephemeral=True)

	async def _handle_demon_interacted(
		self,
		interaction: discord.Interaction,
		response: str,
		status_message: str,
		extra_response: str | None = None,
	) -> None:
		"""
		Handler for when an encounter has finished. Updates the status message and icon count, then
		edits the original parent view message to reflect the outcome.

		Args:
		    interaction (discord.Interaction): The Discord interaction object from the button press.
		    status_message (str): Message to display in the status of the parent view after interaction.
		"""
		# For finished encounters, update the parent_view if we've had a followup.
		parent_view = self._root_view
		parent_view._update_icon_count()

		if parent_view.status_display is not None:
			parent_view.status_display.content = parent_view.status_display.content + f"\n-# `{status_message}`"

		# Update the view messages with information.
		if parent_view is not self:
			# If this is a followup view, update the original message and the ephemeral one.
			if parent_view.message is not None:
				# Update the original message with the new view that has the updated icon count and status message.
				await parent_view.message.edit(view=parent_view)
			else:
				# Should never happen.
				print(f"WARN: parent_view.message is None for demon {self.demon.name}.")
			await interaction.response.edit_message(view=self)
		else:
			# Initial view finished without a followup.
			await interaction.response.edit_message(view=parent_view)

		# Send a final message to the user.
		response = format_dialogue(response, self.demon)

		# Added on PARTY_FULL and TOO_WEAK.
		if extra_response:
			response += f"\n\n-# {extra_response}"

		msg = MessageView(
			f"{response}\n\n-# `{status_message}`",
			self.demon.design_data.encounter_img,
			self.demon.design_data.colour,
		)
		await interaction.followup.send(view=msg, ephemeral=True)

	async def _update_dupe_level(
		self,
		interaction: discord.Interaction,
		demon: DemonData,
		dupe_message: str | None,
	):
		summoner_id = self.summoner_id
		server_id = interaction.guild_id

		if server_id is None:
			raise RuntimeError("Server ID is None.")

		reg_status = await player_demons_queries.check_demon_registration(summoner_id, server_id, demon.id)
		summoned = reg_status in [DemonRegistration.IN_PARTY, DemonRegistration.ON_LOAN]

		if summoned:
			# Add the message for duplicates if it's available.
			if dupe_message:
				player_mention = f"<@{summoner_id}>'s"
				new_level = demon.dupes + 1
				level_string = "MAX" if new_level == 5 else str(new_level)

				msg = MessageView(
					(
						f"### {player_mention} {demon.race} {demon.name} has leveled up to"
						f" {level_string}{Emotes.GEM.value}!"
						f"\n{dupe_message}"
					),
					demon.design_data.profile_img,
					demon.design_data.colour,
				)
				await interaction.followup.send(view=msg)


class EncounterViewInitial(EncounterViewTemplate):
	"""
	Initial encounter view that will spawn with the demon. Has an icon display that represents the number of
	interactions left and a status display that updates with each successful interaction. Once the icon count hits 0,
	the buttons are disabled.
	"""

	def __init__(
		self,
		demon: DemonData,
		summoner_id: int,
		count: int = 1,
		user_exclusive_to: int | None = None,
		tutorial: bool = False,
	) -> None:
		"""
		Init for the initial encounter view.

		Args:
		    demon (DemonData): The encounter's demon information.
		    count (int, optional): The number of interactions before encounter ends. Defaults to 1.
		    user_exclusive_to (int | None, optional): If set, only this user ID can interact with the encounter.
		    tutorial (bool, optional): If set to True, the encounter can't be failed. Defaults to False.
		"""
		super().__init__(demon, summoner_id, count, tutorial=tutorial)

		self.user_exclusive_to = user_exclusive_to
		self.parent_view = self

		# Set to keep track of the users who have interacted with the encounter to prevent multiple interactions.
		self.interacted_users: set[int] = set()
		self.icon_display = discord.ui.TextDisplay((Emotes.ICON.value + " ") * self.count)

		self._build_layout(self.talk_data.question, self.talk_data.answers)

	def _build_layout(self, question: str, dialogue_options: tuple[AnswerData, ...]) -> None:
		"""
		Function to build the view layout for the initial encounter. Creates icons, status display, and dialogue option
		buttons.

		Args:
		    message (str): The initial message to display from the demon.
		    dialogue_options (list[dict]): List of dialogue options, where key is the button 'label' and value is
				'response' that maps Personality types to ResponseType.
		"""

		ui = discord.ui
		container = ui.Container(accent_color=self.demon.design_data.colour)

		# Format text.
		stars = f" ({self.demon.dupes}{Emotes.GEM_THIN.value})" if self.demon.dupes > 0 else ""

		if self.demon.design_data.greeting is not None:
			greeting = format_greeting(self.demon.design_data.greeting, self.demon)
		else:
			greeting = f"{self.demon.race} {self.demon.name}{stars}!"

		question = format_dialogue(question, self.demon)
		details = f"Rank: {self.demon.rank}"

		container.add_item(self.icon_display)
		container.add_item(ui.TextDisplay(f"### {greeting}\n{question}"))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)

		# Add encounter image.
		container.add_item(ui.MediaGallery().add_item(media=self.demon.design_data.encounter_img))

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
		self.status_display = ui.TextDisplay(f"-# {details} {Unicode.BULLET.value} *What will you do?*")
		container.add_item(self.status_display)

		self.add_item(container)

	def _make_dialogue_callback(self, reaction_data: ReactionData):
		"""
		Extension of _make_dialogue_callback from the base view and adds a layer of logic to handle user exclusivity and
		multiple interactions.

		Returns:
		    Callable: Callback function for the dialogue option logic for user exclusivity and multiple interactions.
		"""
		# Explicitly build the callback, not just use super().
		base_callback = EncounterViewTemplate._make_dialogue_callback(self, reaction_data)

		async def callback(interaction: discord.Interaction) -> None:
			"""
			Adds layer of logic to check if encounter is exclusive to a user and to ensure once a user interacts with
			the encounter, they are added to a set and prevented from interacting again.

			Args:
			    interaction (discord.Interaction): The Discord interaction object from the button press.
			"""
			user_id = interaction.user.id

			# Check if user has already interacted.
			if user_id in self.interacted_users:
				await interaction.response.defer()
				return

			# If user isn't the one who the encounter is for (when option exists), exit early.
			if self.user_exclusive_to and user_id != self.user_exclusive_to:
				await interaction.response.defer()
				return

			# We only want the user to be able to interact once with the box,
			# if it's a multi-option encounter, an ephemeral message will be sent next.
			self.interacted_users.add(user_id)

			# Call the original _make_dialogue_callback.
			await base_callback(interaction)

		return callback

	def _update_icon_count(self):
		"""
		Updates icon count display by decrementing count and updating the content. If count hits 0, disable the
		buttons to end the encounter.
		"""
		self.count -= 1

		# This check is necessary as content being empty causes an exception.
		if self.count > 0:
			self.icon_display.content = (Emotes.ICON.value + " ") * self.count
		else:
			self.icon_display.content = Emotes.BLANK.value
			self._disable_buttons()


class EncounterViewFollowup(EncounterViewTemplate):
	"""
	Followup encounter view that spawns on either a neutral or bad response. Similar layout to the initial but without
	icons, media gallery and status display footer. Does not need to know who interaction is exclusive to as it uses
	ephemeral messages.
	"""

	def __init__(
		self,
		demon: DemonData,
		summoner_id: int,
		parent_view: EncounterViewTemplate,
		response: str,
		consecutive_bad: int,
		tutorial: bool = False,
	):
		"""
		Init for the followup encounter view.

		Args:
		    demon (DemonData): The encounter's demon information.
		    parent_view (EncounterViewTemplate): Parent view that spawned this followup, used for updating status and
				icon count on the original message.
		    consecutive_bad (int): Number of consecutive bad interactions that have occurred in the encounter
				so far, used for flee logic. Defaults to 0.
		    tutorial (bool, optional): Whether this encounter is a tutorial encounter, which prevents encounter from
				fleeing. Defaults to False.
		"""
		super().__init__(demon, summoner_id, consecutive_bad_interactions=consecutive_bad, tutorial=tutorial)

		self.response = response
		self.parent_view = parent_view
		self.interacted = False

		self._build_layout(self.talk_data.question, self.talk_data.answers)

	def _build_layout(self, question: str, dialogue_options: tuple[AnswerData, ...]) -> None:
		"""
		Function to build the view layout for the followup encounter.

		Args:
		    message (str): The initial message to display from the demon.
		    dialogue_options (list[dict]): List of dialogue options, where key is the button 'label' and value is
				'response' that maps Personality types to ResponseType.
		"""
		ui = discord.ui
		container = ui.Container(accent_color=self.demon.design_data.colour)

		question = format_dialogue(question, self.demon)
		response = format_dialogue(self.response, self.demon)

		section = ui.Section(accessory=ui.Thumbnail(media=self.demon.design_data.encounter_img))
		section.add_item(ui.TextDisplay(f"{response}\n\n{question}"))

		container.add_item(section)
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)
		self.add_item(container)

	def _make_dialogue_callback(self, reaction_data: ReactionData):
		"""
		Extension of _make_dialogue_callback from the base view and adds a layer of logic to handle disabling buttons
		after an interaction.

		Args:
		    option_index (int): Index of the dialogue option to create the callback for.
		"""
		base_callback = EncounterViewTemplate._make_dialogue_callback(self, reaction_data)

		async def callback(interaction: discord.Interaction) -> None:
			"""
			Adds a layer of logic to disable buttons after an interaction so that the user can only interact with the
			followup once, preventing multiple interactions.

			Args:
			    interaction (discord.Interaction): The Discord interaction object from the button press.
			"""
			if self.interacted:
				await interaction.response.defer()
				return

			self.interacted = True
			self._disable_buttons()
			await base_callback(interaction)

		return callback
