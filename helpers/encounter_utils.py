from entities.player_data import ENCOUNTER_WINDOW_HOURS


def get_current_encounter_window(now: int) -> int:
	"""Get the current encounter window in seconds. Man, this took me way too long."""
	# Convert window hours to seconds.
	window_seconds = ENCOUNTER_WINDOW_HOURS * 3600

	# How many times the window has elapsed since the beginning.
	windows_elapsed = now // window_seconds

	# Take the number of windows elapsed and multiply it by how long a window takes in seconds.
	# We then know which window we're currently in.
	this_window = windows_elapsed * window_seconds

	return this_window
