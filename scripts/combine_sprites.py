import argparse
import random
import sys

from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from helpers.demon_queries import DemonQueries

# Directories for sprites and backgrounds.
SPRITES_DIR = Path(__file__).parent.parent / "sprites"
OUTPUT_DIR = SPRITES_DIR / "output"
BACKGROUNDS_DIR = SPRITES_DIR / "backgrounds"
CHARACTER_DIRS = SPRITES_DIR / "characters"

# Positioning and scaling.
UPSCALE_FACTOR = 5

# Position character horizontally centred.
HORIZONTAL_CENTER = True

# 0 = bottom, 1 = top. 0.6 means slightly above bottom.
VERTICAL_OFFSET = 0.6


def bulk_get_backgrounds(
	number: int = 1,
	indices: list[int] | None = None,
) -> list[Image.Image]:
	"""
	Selects background images to composite the character sprite onto.

	Args:
		number (int, optional): The number of backgrounds to select. Defaults to 1.
		indices (list[int], optional): A list of indices for the backgrounds to choose from.
	Returns:
	    list[Image.Image]: A list of selected background images in RGBA mode.
	"""
	background_files = list(BACKGROUNDS_DIR.glob("*.png")) + list(BACKGROUNDS_DIR.glob("*.gif"))

	if not background_files:
		raise FileNotFoundError(f"No background images found in {BACKGROUNDS_DIR}")

	selected_bgs = []
	if indices:
		for i in indices:
			if i < 0 or i >= len(background_files):
				raise IndexError(f"Background index {i} is out of range: {len(background_files)}.")

			selected_bgs.append(background_files[i])
	else:
		for _ in range(number):
			selected_bgs.append(random.choice(background_files))

	return [get_rgba_sprite(bg) for bg in selected_bgs]


def bulk_find_character_sprites(race: str) -> list[Path]:
	# Characters stored in subdirs by race.
	race_dir = CHARACTER_DIRS / race.lower()

	if not race_dir.exists():
		raise FileNotFoundError(f"Race directory not found: {race_dir}")

	# Search database for characters in a race.
	d_names = DemonQueries().get_demon_names_by_race(race)

	# Match name by using isalnum. (e.g. "Jack O' Lantern" -> "jackolantern")
	d_names = [normalise_name(n) for n in d_names]

	# Find sprites for names from the race.
	for ext in [".gif", ".png"]:
		image_locations = []

		for name in d_names:
			file = race_dir / f"{name}{ext}"

			if not file.exists():
				# Remove it from the list.
				print(f"WARN: Sprite not found for {file.stem}. Removing from list.")
				continue

			image_locations.append(file)

		if image_locations:
			return image_locations

	return []


def normalise_name(name: str) -> str:
	"""Helper to normalise a name by removing non-alphanumeric characters and converting to lowercase."""
	# First n is name and what is used in the loop itself, second n is iteration variable.
	return "".join(n for n in name if n.isalnum()).lower()


def get_rgba_sprite(sprite_path: str | Path) -> Image.Image:
	"""Helper to load a character sprite image."""
	return Image.open(sprite_path).convert("RGBA")


def combine_sprite_on_background(sprite_path: Path, background: Image.Image) -> list[Image.Image]:
	# Upscale the background sprite.
	bg_base = upscale_sprite(background.copy())
	frames = []
	sprite = Image.open(sprite_path)

	try:
		while True:
			# Convert and upscale the character sprite.
			frame = sprite.convert("RGBA")
			frame = upscale_sprite(frame)

			bg_copy = bg_base.copy()

			# Calculate positions to paste character.
			x = (bg_copy.width - frame.width) // 2 if HORIZONTAL_CENTER else 0

			# Cast int due to VERTICAL_OFFSET being a float.
			y = int((bg_copy.height - frame.height) * VERTICAL_OFFSET)

			# Paste character at x, y with alpha mask to preserve transparency.
			bg_copy.paste(frame, (x, y), frame)

			# Append completed frame to list of frames.
			frames.append(bg_copy)

			# Move to next frame.
			sprite.seek(sprite.tell() + 1)
	except EOFError:
		# No more frames in the sprite.
		pass

	return frames if len(frames) > 1 else frames[0]


def upscale_sprite(sprite: Image.Image) -> Image.Image:
	"""Helper to upscale a character sprite."""
	new_w = sprite.width * UPSCALE_FACTOR
	new_h = sprite.height * UPSCALE_FACTOR
	return sprite.resize((new_w, new_h), resample=Image.Resampling.NEAREST)


def save_image(frames: list[Image.Image], filename: str, duration: int = 100):
	"""Helper to save the final image."""
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	output_path = OUTPUT_DIR / filename
	gif = []

	for f in frames:
		gif.append(f.quantize(method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE))

	gif[0].save(output_path, format="GIF", save_all=True, append_images=gif[1:], loop=0, duration=duration)
	print(f"Saved image as {output_path.stem}.gif")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Put character sprites onto backgrounds.")

	char_group = parser.add_mutually_exclusive_group(required=True)
	char_group.add_argument("--name", type=str, help="Name of the demon to place on a background. (e.g. Pixie)")
	char_group.add_argument("--race", type=str, help="Select a whole race to create sprites for. (e.g. Fairy)")

	bg_group = parser.add_mutually_exclusive_group(required=True)
	bg_group.add_argument("--number", type=int, default=1, help="Number of backgrounds to use.")
	bg_group.add_argument("--backgrounds", type=int, nargs="+", help="Background indices (single demon only).")

	args = parser.parse_args()

	# Race mode.
	if args.race:
		character_sprites = bulk_find_character_sprites(args.race)

		total_backgrounds = len(list(BACKGROUNDS_DIR.glob("*.png"))) + len(list(BACKGROUNDS_DIR.glob("*.gif")))
		print(f"\n{total_backgrounds} backgrounds available. Leave blank for random selection.")

		# e.g. pixie: [0, 2, 5], jackolantern: [1, 3, 4]
		char_assignments: dict[str, list[int] | None] = {}
		for char in character_sprites:
			bg_indices = input(f"Enter background indices for {char.stem} (separated by spaces or leave blank for random): ")

			if bg_indices.strip():
				char_assignments[char.stem] = [int(i) for i in bg_indices.split()]
			else:
				char_assignments[char.stem] = None

		for char_path in character_sprites:
			name = char_path.stem
			bg_indices = char_assignments[name]
			backgrounds = bulk_get_backgrounds(number=args.number, indices=bg_indices)
			sprite = get_rgba_sprite(char_path)
			duration = sprite.info.get("duration", 100)  # Default 100ms if not found.

			for i, bg in enumerate(backgrounds):
				composite = combine_sprite_on_background(char_path, bg)
				save_image(composite, f"{name}_{i + 1}.gif", duration)

	else:
		# Single demon mode.
		number = len(args.backgrounds) if args.backgrounds else args.number
		backgrounds = bulk_get_backgrounds(number, indices=args.backgrounds)
		name = normalise_name(args.name)

		# Find the first matching sprite file for the given name and extensions.
		sprite_path = None
		for ext in [".gif", ".png"]:
			check_image = next(CHARACTER_DIRS.rglob(f"{name}{ext}"), None)

			if check_image is not None:
				sprite_path = check_image
				break

		if sprite_path is None:
			raise FileNotFoundError(f"Sprite not found for {name}")

		sprite = get_rgba_sprite(sprite_path)
		duration = sprite.info.get("duration", 100)  # Default 100ms if not found.

		for i, bg in enumerate(backgrounds):
			composite = combine_sprite_on_background(sprite_path, bg)
			save_image(composite, f"{name}_{i + 1}.gif", duration)
