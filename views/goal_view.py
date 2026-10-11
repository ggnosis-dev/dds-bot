import discord

from entities.tutorial_data import TUTORIAL_STEPS, TutorialStep
from shared_enums import EmbedColours, Emotes, Unicode


class GoalView(discord.ui.LayoutView):
	def __init__(self, step: int, task_mask: int):
		super().__init__()
		self.step = step
		self.max_step = 10
		self.task_mask = task_mask
		self.step_data: TutorialStep = TUTORIAL_STEPS[step]

	@classmethod
	async def send(cls, destination, *args) -> discord.Message:
		"""
		Send a message wrapped in an layout view type message.

		Args:
			destination: Where to send message to.
			*args: Required arguments (see init).
			**kwargs: Keyword/optional arguments (see init).
		"""
		try:
			view = cls(*args)
			view._build_layout()
			return await destination.send(view=view)
		except Exception as e:
			raise (e)

	def _build_layout(self) -> None:
		ui = discord.ui
		container = ui.Container(accent_color=EmbedColours.DEFAULT.value)
		sd = self.step_data
		num_tasks = len(sd.desc_tasks)

		container.add_item(
			ui.TextDisplay(
				f"-# `STEP: {self.step} / {self.max_step} {Unicode.BULLET.value} {format(self.task_mask, f'0{num_tasks}b')}`"
				f"\n### **Tutorial:** {sd.desc_step} {Emotes.HUH.value}"
			)
		)
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

		task_list = ""
		for task_id, task in sd.desc_tasks.items():
			# e.g. 6 == 0b011 (task 1 and 2 done).
			# 6 & (1 << (2 - 1))) where 2 is task 2.
			# 0b011 & 0b010 == 0b010 == 2 = truthy
			done = bool(self.task_mask & (1 << (task_id - 1)))
			task_list += f"\n- {'~~' if done else ''}{task.name}{'~~' if done else ''}\n-# {task.hint}"

		container.add_item(ui.TextDisplay(f"{task_list}"))

		# Footer.
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
		container.add_item(ui.TextDisplay(f"-# Reward: **{sd.reward_text}**"))

		self.add_item(container)
