import argparse

from pathlib import Path

from PIL import Image, ImageSequence

from scripts.create_encounter_sprites import bulk_find_character_sprites, normalise_name, save_image, upscale_sprite

# Directories for sprites and backgrounds.
SPRITES_DIR = Path(__file__).parent.parent / "sprites"
OUTPUT_DIR = SPRITES_DIR / "output"
CHARACTER_DIRS = SPRITES_DIR / "characters"
PROFILE_BG = SPRITES_DIR / "profile_sprites/profile_bg.png"

# Scaling constants.
BG_UPSCALE_FACTOR = 2
UPSCALE_FACTOR = 2

# Positioning constants.
# 0 = bottom, 1 = top. 0.5 means middle
VERTICAL_OFFSET = 0.5


def combine_sprite_on_background(sprite: Image.Image) -> list[Image.Image]:
	# Upscale the background sprite.
	bg = Image.open(PROFILE_BG).convert("RGBA")
	# bg = ImageEnhance.Brightness(bg_base).enhance(BG_BRIGHTNESS)
	bg = upscale_sprite(bg, BG_UPSCALE_FACTOR)

	frames = []

	for frame in ImageSequence.Iterator(sprite):
		# Convert and upscale the character sprite.
		frame = frame.convert("RGBA")
		frame = upscale_sprite(frame, UPSCALE_FACTOR)

		bg_copy = bg.copy()

		# Calculate positions to paste character.
		x = (bg_copy.width - frame.width) // 2

		# Cast int due to VERTICAL_OFFSET being a float.
		y = int((bg_copy.height - frame.height) * VERTICAL_OFFSET)

		# Paste character at x, y with alpha mask to preserve transparency.
		bg_copy.paste(frame, (x, y), frame)

		# Append completed frame to list of frames.
		frames.append(bg_copy)

	return frames if len(frames) > 1 else frames[0]


def get_sprite(name: str) -> list[Path]:
	name = normalise_name(name)

	# Find the first matching sprite file for the given name and extensions.
	sprite_path = None
	for ext in [".gif", ".png"]:
		check_image = next(CHARACTER_DIRS.rglob(f"{name}{ext}"), None)

		if check_image is not None:
			sprite_path = check_image
			break

	if sprite_path is None:
		raise FileNotFoundError(f"Sprite not found for {name}")

	return [sprite_path]


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Put character sprites onto a profile backgrounds.")

	char_group = parser.add_mutually_exclusive_group(required=True)
	char_group.add_argument("--name", type=str, help="Name of the demon to place on a profile. (e.g. Pixie)")
	char_group.add_argument("--race", type=str, help="Select a whole race to create sprites for. (e.g. Fairy)")

	args = parser.parse_args()

	demon_sprites = get_sprite(args.name) if args.name else bulk_find_character_sprites(args.race)

	for char_path in demon_sprites:
		name = char_path.stem
		sprite = Image.open(char_path)

		# Get the duration of the GIF. Default 100ms if not found.
		duration = sprite.info.get("duration", 100)

		composite = combine_sprite_on_background(sprite)
		save_image(composite, f"{name}_pr.gif", duration)

		print(f"INFO: Created new Profile GIF for {name}")
