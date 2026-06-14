import argparse
import random
import re
import sys

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

sys.path.insert(0, str(Path(__file__).parent.parent))
from queries.demon_queries import DemonQueries

# Directories for sprites and backgrounds.
SPRITES_DIR = Path(__file__).parent.parent / "sprites"
OUTPUT_DIR = SPRITES_DIR / "output"
BACKGROUNDS_DIR = SPRITES_DIR / "backgrounds"
CHARACTER_DIRS = SPRITES_DIR / "characters"

# Scaling constants.
BG_UPSCALE_FACTOR = 3
UPSCALE_FACTOR = 3

# Positioning constants.
# Position character in the centre.
HORIZONTAL_OFFSET = 0.5

# 1 = bottom, 0 = top.
VERTICAL_OFFSET = 0.4

# Crop constants.
BG_VERTICAL_START = 0.8
CROP_WIDTH = 238
CROP_HEIGHT = 108

# Design constants.
BORDER_SIZE = 1
BORDER_COLOUR = 0xFFFFFF
BG_BRIGHTNESS = 1


def extract_number(file: Path) -> int:
	"""Using regex, extract first number. If no number found, return -1."""
	match = re.search(r"\d+", file.stem)
	return int(match.group()) if match else -1


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
	files = list(BACKGROUNDS_DIR.glob("*.png")) + list(BACKGROUNDS_DIR.glob("*.gif"))

	# Sort backgrounds numerically.
	files = sorted(files, key=extract_number)

	if not files:
		raise FileNotFoundError(f"No background images found in {BACKGROUNDS_DIR}")

	selected_bgs = []
	if indices:
		for i in indices:
			if i < 0 or i >= len(files):
				raise IndexError(f"Background index {i} is out of range: {len(files)}.")

			selected_bgs.append(files[i])
	else:
		for _ in range(number):
			selected_bgs.append(random.choice(files))

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
	image_locations = []
	for name in d_names:
		for ext in [".gif", ".png"]:
			file = race_dir / f"{name}{ext}"

			if file.exists():
				image_locations.append(file)
				break

			print(f"WARN: Sprite not found for {name}{ext}.")

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
	bg_base = background.copy()
	bg_base = crop_from_bottom(bg_base, CROP_WIDTH, CROP_HEIGHT, BG_VERTICAL_START)
	bg_base = ImageEnhance.Brightness(bg_base).enhance(BG_BRIGHTNESS)
	bg_base = upscale_sprite(bg_base, BG_UPSCALE_FACTOR)
	bg_base = tile_background(bg_base, int(CROP_WIDTH * BG_UPSCALE_FACTOR), int(CROP_HEIGHT * BG_UPSCALE_FACTOR))

	frames = []
	sprite = Image.open(sprite_path)

	try:
		while True:
			# Convert and upscale the character sprite.
			frame = sprite.convert("RGBA")
			frame = upscale_sprite(frame, UPSCALE_FACTOR)

			bg_copy = bg_base.copy()

			# Calculate positions to paste character.
			x = int((bg_copy.width - frame.width) * HORIZONTAL_OFFSET)

			# Cast int due to VERTICAL_OFFSET being a float.
			y = int((bg_copy.height - frame.height) * VERTICAL_OFFSET)

			# Paste character at x, y with alpha mask to preserve transparency.
			bg_copy.paste(frame, (x, y), frame)

			# Add a border.
			bg_copy = add_border(bg_copy, BORDER_COLOUR)

			# Append completed frame to list of frames.
			frames.append(bg_copy)

			# Move to next frame.
			sprite.seek(sprite.tell() + 1)
	except EOFError:
		# No more frames in the sprite.
		pass

	print(f"INFO: Created new GIF for {sprite_path}")
	return frames if len(frames) > 1 else frames[0]


def tile_background(tile: Image.Image, target_width: int, target_height: int) -> Image.Image:
	# Get the image's width and heights.
	tile_w, tile_h = tile.size

	# Instance of new image.
	tiled = Image.new("RGBA", (target_width, target_height))

	# Find the centre of the main tile so we know where to put tiles around it.
	target_centre_x = target_width // 2

	# Find the edge of the main tile. This should also reflect how much space is on either side of the main tile.
	edge_x = target_centre_x - tile_w // 2

	# Bottom edge of the main. We ignore the divided by 2 as we want to anchor this to the bottom.
	edge_y = target_height - tile_h

	# By subtracting the tile's coordinates from the edge, we can get location of the first tile.
	start_x = edge_x - tile_w
	start_y = edge_y - tile_h

	# For the amount of times that tile_height can fit between the start_y and target_height.
	for row, y in enumerate(range(start_y, target_height, tile_h)):
		# Rotate the tile by 180 for every second row. row mod 2 will return False when 0, True when 1.
		current_tile = tile.rotate(180) if not row % 2 else tile

		for x in range(start_x, target_width, tile_w):
			tiled.paste(current_tile, (x, y))

	return tiled


def add_border(image: Image.Image, colour: int) -> Image.Image:
	return ImageOps.expand(image, border=BORDER_SIZE, fill=colour)


def crop_from_bottom(image: Image.Image, width: int, height: int, vertical_start: float) -> Image.Image:
	"""
	Helper to crop background image anchored from the bottom to a specific width and height.

	Args:
		image (Image.Image): Image to crop.
		width (int): Desired region's width.
		height (int): Desired region's height.
		vertical_start (float): Vertical starting position as a fraction of the image height.
	Returns:
		Image.Image: Cropped image.
	"""
	top = int(image.height * vertical_start)
	top = min(top, image.height - height)
	left = (image.width - width) // 2

	image = image.crop((left, top, left + width, top + height))
	bounding_box = image.getbbox()
	return image.crop(bounding_box)


def upscale_sprite(sprite: Image.Image, factor: int) -> Image.Image:
	"""Helper to upscale a character sprite."""
	new_w = sprite.width * factor
	new_h = sprite.height * factor
	return sprite.resize((new_w, new_h), resample=Image.Resampling.NEAREST)


def save_image(frames: list[Image.Image] | Image.Image, filename: str, duration: int = 100) -> None:
	"""
	Helper to save the final image.

	Args:
		frames (list[Image.Image] | Image.Image) Combined image(s) of sprites. PNGs will be one frame, hence Image.Image.
		filename (str): The filename to save the final image as.
		duration (int): The frame delay of the GIF. Defaults to 100ms.
	"""
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	output_path = OUTPUT_DIR / filename
	gif = []

	if isinstance(frames, Image.Image):
		gif.append(quantize_frame(frames))
	else:
		for f in frames:
			gif.append(quantize_frame(f))

	gif[0].save(
		output_path,
		format="GIF",
		save_all=True,
		append_images=gif[1:],
		loop=0,
		duration=duration,
		# Prevent PIL from compressing palette across frames (which can corrupt the palette)
		optimize=False,
	)
	print(f"Saved image as {output_path.stem}.gif")


def quantize_frame(frame: Image.Image) -> Image.Image:
	"""
	Helper to quantize the image. Frames use .quantize to reduce image colour to 256 colors required by GIFs using the
	"octree" method (fast variation). Dithering is also disabled to make pixels sharper.
	"""
	return frame.quantize(method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)


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

		# e.g. pixie: [1, 2, 5], jackolantern: [1, 3, 4]
		char_assignments: dict[str, list[int] | None] = {}
		for char in character_sprites:
			# Retry loop.
			while True:
				# Get input from the user.
				bg_indices = input(
					f"Enter background indices for {char.stem} (separated by spaces or leave blank for random): "
				)

				# If blank, assign None and continue to next character.
				if not bg_indices.strip():
					char_assignments[char.stem] = None
					break

				try:
					# Get list of integers from input.
					indices = [int(i) for i in bg_indices.split()]

					# If outside valid range, ask again.
					invalid = [i for i in indices if i < 0 or i >= total_backgrounds]
					if invalid:
						print(f"Invalid indices: {invalid}. Enter valid indices.")
						continue

					char_assignments[char.stem] = indices
					break
				except ValueError:
					print("Invalid input. Enter valid integers separated by spaces.")
					continue

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
