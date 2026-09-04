import asyncio

from abc import ABC, abstractmethod

import discord

from entities.demon_data import DemonData
from entities.encounter_data import BUTTON_EMOTES, AnswerData, ReactionData, TalkData
from helpers import encounter_utils
from helpers.format_utils import format_dialogue, format_greeting
from helpers.messages import EncountersMsg as Messages
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
		talk_data: TalkData,
		*,
		count: int = 1,
		consecutive_bad_interactions: int = 0,
		tutorial: bool = False,
	) -> None:
		"""
		Init for the base encounter view.

		Args:
			demon (DemonData): The encounter's demon information.
			summoner_id (int): Used to lock potential dupes to the player who summoned it.
			message (discord.Message): Message the encounter is associated with, needed for editing and followups.
			count (int): Number of recruitable demons in the one encounter.
			consecutive_bad_interactions (int, optional): Threshold that dictates when a demon will flee.
			tutorial (bool, optional): Whether to treat this as a tutorial encounter, which has different flee logic.
		"""
		super().__init__(timeout=ENCOUNTER_TIMEOUT)

		self.demon = demon
		self.summoner_id = summoner_id
		self.count = count
		self.consecutive_bad_interactions = consecutive_bad_interactions
		self.tutorial = tutorial
		self.talk_data = talk_data

		# Message gets set during start function.
		self.message: discord.Message | None = None
		# List of the view's option sections. Built in _build_option_buttons
		self.option_sections: list = []

		self.status_display: discord.ui.TextDisplay | None = None
		self.parent_view: EncounterViewTemplate | None = None

	@classmethod
	async def start(
		cls,
		destination: discord.abc.Messageable,
		demon: DemonData,
		summoner_id: int,
		*args,
		**kwargs,
	) -> discord.Message:
		"""Send the encounter view. Builds talk data before initialising class fully. Assigns self.message."""
		try:
			# Retrieve the dialogue the demon will say.
			talk_data = await talk_queries.get_talk_dialogue(demon.tone_type.value, demon.personality_type.value)

			# Prepare the view.
			view = cls(demon, summoner_id, talk_data, *args, **kwargs)

			# Send the message and assign it.
			message = await destination.send(view=view)
			view.message = message
			return message
		except Exception as e:
			raise RuntimeError(f"Encounter not sent. {e}")

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

	def _build_option_buttons(self, container: discord.ui.Container, answers: tuple[AnswerData, ...]) -> None:
		"""
		Build dialogue option sections into the container with its button and attached callback.

		Args:
			answers (tuple[AnswerData, ...]): Key is the button 'label' and value is a list of ReactionData.
		"""
		# List of the view's option sections. Initialised/Reinit here.
		self.option_sections = []

		# For each possible answer, add a section for it.
		for i, answer in enumerate(answers, 0):
			button = discord.ui.Button(
				emoji=BUTTON_EMOTES[i].value,
				style=discord.ButtonStyle.grey,
			)

			# Callback should know data about the reaction.
			reaction_data = answer.reactions[0]
			button.callback = self._make_dialogue_callback(reaction_data)

			# Build section into the view.
			new_section = discord.ui.Section(accessory=button)
			new_section.add_item(discord.ui.TextDisplay(f"{answer.label}"))
			container.add_item(new_section)

			# Store dialogue options to access them in the various callbacks.
			self.option_sections.append(new_section)

	def _disable_buttons(self) -> None:
		"""Helper function to disable all buttons in a view."""
		for section in self.option_sections:
			section.accessory.disabled = True

	def _make_dialogue_callback(self, reaction_data: ReactionData):
		"""
		Factory for dialogue button's callback.

		Args:
			reaction_data (ReactionData): Each button needs persistent reaction_data to determine its outcome.
		"""

		async def callback(interaction: discord.Interaction) -> None:
			"""
			Callback function for when a dialogue option button is pressed. Determines the outcome and updates accordingly.

			Args:
				interaction (discord.Interaction): Discord interaction object from the button press.
			"""
			# Get the answer using the stored reaction data.
			r_type = reaction_data.response_type
			r_text = reaction_data.response

			# If there are no demons available in the count.
			if self._root_view.count <= 0:
				# Acknowledge the response.
				await interaction.response.defer()

				# Tell player all demons are gone.
				await MessageView.reply(
					interaction,
					Messages.all_demons_gone(),
					colour=self.demon.design_data.colour,
					ephemeral=True,
				)
				return

			# If demons still available, check their response type to the answer.
			match r_type:
				case ResponseType.GOOD:
					await self._encounter_successful(interaction, r_text)

				case ResponseType.NEUTRAL | ResponseType.BAD:
					# Bad count will be sent to followup views and become unique to each player after Initial.
					new_bad_count = self.consecutive_bad_interactions + BAD_COUNT_INCREMENT[r_type]

					# Flee or followup logic.
					if new_bad_count >= FLEE_THRESHOLD and not self.tutorial:
						await self._encounter_flee(interaction, r_text)
					else:
						await self._encounter_followup(interaction, r_text, new_bad_count)

		return callback

	async def _encounter_successful(self, interaction: discord.Interaction, demon_response: str) -> None:
		"""
		Adds to party and/or compendium, sends message confirming the demon has joined and tries to add dupe level.

		Args:
			demon_response (str): What the demon will say back.
		"""
		join_data = await encounter_utils.join_player_party(interaction.user, interaction.guild, self.demon)

		await asyncio.gather(
			self._handle_demon_interacted(
				interaction,
				demon_response,
				join_data.status_message,
				join_data.extra_response,
			),
			self._update_dupe_level(interaction, join_data.dupe_message),
		)

	async def _encounter_flee(self, interaction: discord.Interaction, demon_response: str) -> None:
		"""Sends an ephemeral message that the demon has fled and updates the status."""
		status_message = Messages.demon_fled(self.demon.race, self.demon.name, interaction.user.name)
		await self._handle_demon_interacted(interaction, demon_response, status_message)

	async def _encounter_followup(self, interaction: discord.Interaction, demon_response: str, new_bad_count: int) -> None:
		"""
		Creates a new ephemeral message with new dialogue options. Occurs on responses that haven't hit the flee threshold.

		Args:
			response (str): What the demon will say back.
			new_bad_count (int): Unique bad count for the player to be passed into future views.
		"""
		# For followup encounters, keep track of the parent view for its status updates.
		parent_view = self._root_view

		new_talk_data = await talk_queries.get_talk_dialogue(self.demon.tone_type.value, self.demon.personality_type.value)

		# Build the followup view.
		followup_view = EncounterViewFollowup(
			self.demon,
			self.summoner_id,
			new_talk_data,
			consecutive_bad_interactions=new_bad_count,
			demon_response=demon_response,
			parent_view=parent_view,
			tutorial=self.tutorial,
		)

		# Before followups, we want to make sure buttons from this one will get disabled.
		if isinstance(self, EncounterViewFollowup):
			# Edit the existing ephemeral message to disable buttons, then send the next one.
			await interaction.response.edit_message(view=self)
			await interaction.followup.send(view=followup_view, ephemeral=True)
		else:
			# This is the initial view, which we don't want to edit in case someone ELSE interacts with it.
			await interaction.response.send_message(view=followup_view, ephemeral=True)

	async def _handle_demon_interacted(
		self,
		interaction: discord.Interaction,
		demon_response: str,
		status_message: str,
		extra_response: str | None = None,
	) -> None:
		"""
		Updates the status message and icon count, then edits the initial view message to reflect the outcome.

		Args:
			demon_response (str): What the demon will say back in followup.
			status_message (str): Message to display in the status of the parent view after interaction.
			extra_response (str | None): Append an extra message if needed, such as a TOO WEAK message.
		"""
		# Get parent view so we can update the INITIAL view in the event all count is gone.
		parent_view = self._root_view

		# Update the icon count to reflect that a demon has been interacted with.
		parent_view._update_icon_count()

		# status_display needs to be set first up (done in initial _build_layout).
		if parent_view.status_display is not None:
			parent_view.status_display.content = parent_view.status_display.content + f"\n-# `{status_message}`"

		# Update the view messages with information.
		if parent_view is not self:
			assert parent_view.message is not None, "Root view must use start() before followups can occur."

			await asyncio.gather(
				# Try update the original message with the updated icon count and status message.
				parent_view.message.edit(view=parent_view),
				# If a followup, edit message to show visible changes to button state.
				interaction.response.edit_message(view=self),
			)

		else:
			# Initial view finished without a followup.
			await interaction.response.edit_message(view=parent_view)

		# Send a final message to the user.
		demon_response = format_dialogue(demon_response, self.demon)

		# Added on PARTY_FULL and TOO_WEAK.
		if extra_response:
			demon_response += f"\n\n-# {extra_response}"

		# Build final message.
		message = f"{demon_response}\n\n-# `{status_message}`"
		await MessageView.reply(
			interaction,
			message,
			thumbnail=self.demon.design_data.encounter_img,
			colour=self.demon.design_data.colour,
			ephemeral=True,
		)

	async def _update_dupe_level(
		self,
		interaction: discord.Interaction,
		dupe_message: str | None,
	) -> None:
		"""Check if demon is summoned and grant level up if summoner ID matches interacting player ID."""
		interacting_player_id = interaction.user.id
		if self.summoner_id != interacting_player_id:
			return

		server_id = interaction.guild_id
		if server_id is None:
			raise RuntimeError("Server ID is None.")

		d = self.demon

		# Check if demon is already summoned.
		reg_status = await player_demons_queries.check_demon_registration(self.summoner_id, server_id, d.id)
		is_summoned = reg_status in {DemonRegistration.IN_PARTY, DemonRegistration.ON_LOAN, DemonRegistration.LEADER}

		# Try applying dupe level.
		if is_summoned:
			dupe_message = await encounter_utils.grant_dupe_reward(self.summoner_id, server_id, d)

			# Send dupe message if it exists.
			if dupe_message is not None:
				destination_channel = interaction.channel

				assert isinstance(destination_channel, discord.abc.Messageable), (
					"Interaction had to be in a channel already."
				)

				await MessageView.send(
					destination_channel,
					Messages.dupe_level_up(self.summoner_id, d, dupe_message),
					thumbnail=d.design_data.profile_img,
					colour=d.design_data.colour,
				)


class EncounterViewInitial(EncounterViewTemplate):
	"""
	The first encounter view that will spawn with the demon and its data. Has an icon display that represents the number of
	available demons recruitable and a status display that updates with each complete interaction. Once icon count hits 0,
	the buttons are disabled.
	"""

	def __init__(
		self,
		demon: DemonData,
		summoner_id: int,
		talk_data: TalkData,
		*,
		count: int = 1,
		user_exclusive_to: int | None = None,
		tutorial: bool = False,
	) -> None:

		super().__init__(demon, summoner_id, talk_data, count=count, tutorial=tutorial)
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
	Followup encounter view that spawns if not yet reached flee threshold. Similar layout to the initial but without
	icons, media gallery and status display footer. Does not need to know who interaction is exclusive to as it uses
	ephemeral messages. Defaults to 1 count now that it is separated.
	"""

	def __init__(
		self,
		demon: DemonData,
		summoner_id: int,
		talk_data: TalkData,
		*,
		consecutive_bad_interactions: int,
		demon_response: str,
		parent_view: EncounterViewTemplate,
		tutorial: bool = False,
	):
		"""
		Init for the followup encounter view.

		Args:
			consecutive_bad_interactions (int): Threshold that dictates when a demon will flee. Unique to interacting now.
			demon_response (str): Dialogue delivered back from the demon from last option.
			parent_view (EncounterViewTemplate): Parent view that spawned this one, needed for updates and edits to it.
			tutorial (bool, optional): Whether to treat this as a tutorial encounter, which has different flee logic.
		"""
		super().__init__(
			demon, summoner_id, talk_data, consecutive_bad_interactions=consecutive_bad_interactions, tutorial=tutorial
		)

		self.demon_response = demon_response
		self.parent_view = parent_view
		self.interacted = False

		self._build_layout(self.talk_data.question, self.talk_data.answers)

	def _build_layout(self, question: str, dialogue_options: tuple[AnswerData, ...]) -> None:
		"""
		Function to build the view layout for the followup encounter.

		Args:
			question (str): Dialogue to display from the demon.
			dialogue_options (tuple[AnswerData, ...]): Key is the button 'label' and value is a list of ReactionData.
		"""
		ui = discord.ui
		container = ui.Container(accent_color=self.demon.design_data.colour)

		question = format_dialogue(question, self.demon)
		response = format_dialogue(self.demon_response, self.demon)

		section = ui.Section(accessory=ui.Thumbnail(media=self.demon.design_data.encounter_img))
		section.add_item(ui.TextDisplay(f"{response}\n\n{question}"))

		container.add_item(section)
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		self._build_option_buttons(container, dialogue_options)
		self.add_item(container)

	def _make_dialogue_callback(self, reaction_data: ReactionData):
		"""
		Extension of _make_dialogue_callback from the base view. Adds logic to handle disabling buttons after an interaction.

		Args:
			reaction_data (ReactionData): Each button needs persistent reaction_data to determine its outcome.
		"""
		base_callback = EncounterViewTemplate._make_dialogue_callback(self, reaction_data)

		async def callback(interaction: discord.Interaction) -> None:
			"""
			Adds logic to disable buttons after an interaction so that the user can only interact with the
			followup once, preventing multiple interactions.
			"""
			if self.interacted:
				await interaction.response.defer()
				return

			self.interacted = True
			self._disable_buttons()
			await base_callback(interaction)

		return callback
