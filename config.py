import argparse
import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamConfig:
    width: int
    height: int
    fps: int

    @property
    def resolution(self) -> tuple[int, int]:
        return (self.width, self.height)


def parse_stream_config(argv: list[str] | None = None) -> StreamConfig:
    parser = argparse.ArgumentParser(description="Raspberry Pi camera streaming server")
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.json",
        help="Path to JSON config file",
    )
    parser.add_argument("--width", type=int, default=None, help="Video width in pixels")
    parser.add_argument("--height", type=int, default=None, help="Video height in pixels")
    parser.add_argument("--fps", type=int, default=None, help="Frames per second")
    args = parser.parse_args(argv)

    # Start with defaults
    width = 640
    height = 480
    fps = 30

    # Override with JSON config if provided and exists
    if args.config and os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)
        width = int(config_data.get("width", width))
        height = int(config_data.get("height", height))
        fps = int(config_data.get("fps", fps))

    # Override with CLI args if explicitly provided (highest priority)
    if args.width is not None:
        width = args.width
    if args.height is not None:
        height = args.height
    if args.fps is not None:
        fps = args.fps

    if width <= 0 or height <= 0 or fps <= 0:
        raise ValueError("width, height, and fps must be positive integers")

    return StreamConfig(width=width, height=height, fps=fps)
