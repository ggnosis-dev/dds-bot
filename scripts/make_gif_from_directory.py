"""
Take a directory and convert groups of frames into GIFs. Frames should be named in numeric order (e.g. frame_001.png,
frame_002.png, etc.) and the number of frames per animation should be specified.
"""

import argparse
import re

from pathlib import Path

from PIL import Image


def load_frames(paths: list[Path]) -> list[Image.Image]:
	frames = [Image.open(p).convert("RGBA") for p in paths]

	max_w = max(f.width for f in frames)
	max_h = max(f.height for f in frames)

	anchored = []
	for frame in frames:
		canvas = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
		x = (max_w - frame.width) // 2  # center horizontally
		y = max_h - frame.height  # anchor to bottom
		canvas.paste(frame, (x, y))
		anchored.append(canvas)

	return anchored


def save_gif(frames: list[Image.Image], output_path: Path, fps: int):
	duration_ms = int(1000 / fps)
	frames[0].save(
		output_path,
		save_all=True,
		append_images=frames[1:],
		duration=duration_ms,
		loop=0,
		disposal=2,
	)


def batch_gif(input_dir: str, frames_per_animation: int, fps: int, output_dir: str):
	input_path = Path(input_dir)
	output_path = Path(output_dir)
	output_path.mkdir(parents=True, exist_ok=True)

	all_files = sorted(
		(f for f in input_path.iterdir() if f.suffix.lower() in (".png", ".gif")),
		key=lambda f: tuple(int(n) for n in re.findall(r"\d+", f.stem)),
	)

	if len(all_files) % frames_per_animation != 0:
		print(f"Warning: {len(all_files)} images doesn't divide evenly into groups of {frames_per_animation}.")

	for i, chunk in enumerate(zip(*[iter(all_files)] * frames_per_animation)):
		frames = load_frames(list(chunk))
		out = output_path / f"{i + 1:03d}.gif"
		save_gif(frames, out, fps)
		print(f"Saved {out.name} ({chunk[0].name} > {chunk[-1].name})")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Batch images into GIFs by frame groups.")
	parser.add_argument("input_dir", type=str, help="Directory of input frames.")
	parser.add_argument("--frames-per-animation", "-f", type=int, required=True, help="Number of frames the animation has.")
	parser.add_argument("--fps", type=int, help="Frames per second (default: 12).", default=12)
	parser.add_argument("--output-dir", "-o", type=str, help="Output directory (default: output/).", default="output")
	args = parser.parse_args()

	batch_gif(args.input_dir, args.frames_per_animation, args.fps, args.output_dir)
