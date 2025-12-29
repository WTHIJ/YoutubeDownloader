#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
yt_downloader.py
----------------
Small command-line utility to download a YouTube video in the best possible
quality, with colored, "pip-like" progress bars using tqdm (no rich).

Behavior:
- If ffmpeg is available and there is a higher-resolution adaptive video
  (video-only) stream than the best progressive stream:
    -> download best video-only + best audio-only (each with its own progress bar),
       then merge them with ffmpeg into a final MP4.
- Otherwise:
    -> download the best progressive (video + audio) stream with a progress bar.

Basic usage:
    python yt_downloader.py "YOUTUBE_VIDEO_URL"

Options:
    -o / --output : output directory (default: ./downloads)
"""

import argparse
import os
import re
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pytubefix import YouTube
from pytubefix.exceptions import PytubeFixError
from tqdm import tqdm


# ---------------------------------------------------------------------------
# ANSI colors (for a more vivid CLI output)
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

TAG_INFO = f"{CYAN}[+]{RESET}"
TAG_OK = f"{GREEN}[✓]{RESET}"
TAG_WARN = f"{YELLOW}[!]{RESET}"
TAG_ERR = f"{RED}[-]{RESET}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Return a filesystem-safe version of a string."""
    name = re.sub(r'[\\/*?:"<>|]', replacement, name)
    name = name.strip()[:200]
    return name or "video"


def resolution_value(stream) -> int:
    """Return the numeric resolution (e.g. '1080p' -> 1080) or 0 if unknown."""
    if not stream or not getattr(stream, "resolution", None):
        return 0
    try:
        return int(stream.resolution.replace("p", ""))
    except ValueError:
        return 0


def is_ffmpeg_available() -> bool:
    """Return True if ffmpeg is available on PATH."""
    return shutil.which("ffmpeg") is not None


def create_progress_bar(
    total_bytes: Optional[int],
    desc: str,
    position: int = 0,
    colour: str = "green",
) -> tqdm:
    """
    Create a tqdm progress bar with a 'pip-like' style:

    - colored bar
    - shows downloaded size, total size, speed, elapsed time
    """
    if total_bytes is None:
        total_bytes = 0

    return tqdm(
        total=total_bytes,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=desc,
        ascii=False,
        position=position,
        leave=True,
        colour=colour,      # remove if tqdm version is too old
        dynamic_ncols=True,
        bar_format=(
            "{l_bar}{bar} "
            "{n_fmt}/{total_fmt} "
            "{rate_fmt} "
            "{elapsed}"
        ),
    )


def download_with_progress(
    yt: YouTube,
    stream,
    output_dir: Path,
    description: str,
    filename: Optional[str] = None,
    colour: str = "green",
) -> Path:
    """
    Download a single stream (video-only or audio-only or progressive)
    with a progress bar using pytubefix's on_progress_callback.

    Returns the Path to the downloaded file.
    """
    total_size = getattr(stream, "filesize", None)
    if total_size is None:
        total_size = getattr(stream, "filesize_approx", None)

    progress_bar = create_progress_bar(total_size, desc=description, colour=colour)

    last_bytes_remaining = total_size or 0

    def on_progress(_stream, _chunk, bytes_remaining: int) -> None:
        nonlocal last_bytes_remaining
        if total_size is None:
            downloaded_now = len(_chunk)
        else:
            downloaded_now = last_bytes_remaining - bytes_remaining
            last_bytes_remaining = bytes_remaining

        if downloaded_now > 0:
            progress_bar.update(downloaded_now)

    yt.register_on_progress_callback(on_progress)

    try:
        file_path_str = stream.download(
            output_path=str(output_dir),
            filename=filename,
        )
    finally:
        progress_bar.close()

    return Path(file_path_str)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def download_video(url: str, output_dir: str = "downloads") -> None:
    """
    Download a YouTube video.

    - If ffmpeg is available and a higher-resolution adaptive stream exists:
        * download best video-only stream (with progress bar)
        * download best audio-only stream (with progress bar)
        * merge both using ffmpeg into a final MP4
    - Otherwise:
        * download the best progressive (video + audio) stream
          with a progress bar.
    """
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    try:
        print(f"{TAG_INFO} {BOLD}Fetching video info…{RESET}")
        yt = YouTube(url)
        title = yt.title or "video"
        safe_title = sanitize_filename(title)
        print(f"{TAG_INFO} Title: {BOLD}{title}{RESET}")

        # Best progressive stream (video + audio together)
        progressive_stream = (
            yt.streams
            .filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )

        # Best adaptive video-only stream
        video_stream = (
            yt.streams
            .filter(only_video=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )

        # Best adaptive audio-only stream (any extension)
        audio_stream = (
            yt.streams
            .filter(only_audio=True)
            .order_by("abr")
            .desc()
            .first()
        )

        prog_res = resolution_value(progressive_stream)
        video_res = resolution_value(video_stream)

        print(f"{TAG_INFO} Best progressive stream: {BOLD}{prog_res or 'N/A'}p{RESET}")
        print(f"{TAG_INFO} Best adaptive video-only stream: {BOLD}{video_res or 'N/A'}p{RESET}")
        print(f"{TAG_INFO} ffmpeg available: {BOLD}{is_ffmpeg_available()}{RESET}")

        use_adaptive = (
            is_ffmpeg_available()
            and video_stream is not None
            and audio_stream is not None
            and video_res > prog_res
        )

        # ------------------------------------------------------------------
        # High quality mode: separate video + audio, then merge with ffmpeg
        # ------------------------------------------------------------------
        if use_adaptive:
            print(
                f"\n{TAG_INFO} {BOLD}{GREEN}Using high-quality adaptive mode"
                f" (video + audio + ffmpeg merge).{RESET}"
            )

            # -------------------------
            # Download video-only part
            # -------------------------
            video_ext = video_stream.subtype or "mp4"
            video_filename = f"{yt.video_id}_video.{video_ext}"
            video_size = getattr(video_stream, "filesize", None) or getattr(
                video_stream, "filesize_approx", None
            )
            if video_size:
                print(
                    f"{TAG_INFO} Video size: "
                    f"{BOLD}{video_size / (1024 * 1024):.2f} MB{RESET}"
                )

            video_path = download_with_progress(
                yt=yt,
                stream=video_stream,
                output_dir=output_dir_path,
                description="Downloading video",
                filename=video_filename,
                colour="green",
            )

            # -------------------------
            # Download audio-only part
            # -------------------------
            audio_ext = audio_stream.subtype or "m4a"
            audio_filename = f"{yt.video_id}_audio.{audio_ext}"
            audio_size = getattr(audio_stream, "filesize", None) or getattr(
                audio_stream, "filesize_approx", None
            )
            if audio_size:
                print(
                    f"{TAG_INFO} Audio size: "
                    f"{BOLD}{audio_size / (1024 * 1024):.2f} MB{RESET}"
                )

            audio_path = download_with_progress(
                yt=yt,
                stream=audio_stream,
                output_dir=output_dir_path,
                description="Downloading audio",
                filename=audio_filename,
                colour="cyan",
            )

            # -------------------------
            # Merge with ffmpeg
            # -------------------------
            final_path = output_dir_path / f"{safe_title}.mp4"
            print(
                f"\n{TAG_INFO} Merging video and audio with ffmpeg into: "
                f"{BOLD}{final_path.name}{RESET}"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(audio_path),
                "-c",
                "copy",
                str(final_path),
            ]
            subprocess.run(cmd, check=True)

            # Optionally remove temporary files
            try:
                video_path.unlink(missing_ok=True)
                audio_path.unlink(missing_ok=True)
            except TypeError:
                if video_path.exists():
                    video_path.unlink()
                if audio_path.exists():
                    audio_path.unlink()

            print(f"\n{TAG_OK} Download and merge completed!")
            print(f"{TAG_INFO} Final file: {BOLD}{final_path.resolve()}{RESET}")

        # ------------------------------------------------------------------
        # Fallback: single progressive stream with its own progress bar
        # ------------------------------------------------------------------
        else:
            print(
                f"\n{TAG_WARN} {BOLD}{YELLOW}Using progressive mode"
                f" (single file: video + audio).{RESET}"
            )

            if progressive_stream is None:
                print(f"{TAG_ERR} Could not find a suitable video stream.")
                sys.exit(1)

            file_size = getattr(progressive_stream, "filesize", None) or getattr(
                progressive_stream, "filesize_approx", None
            )
            if file_size:
                print(
                    f"{TAG_INFO} Resolution: {BOLD}{progressive_stream.resolution}{RESET}"
                )
                print(
                    f"{TAG_INFO} Size: "
                    f"{BOLD}{file_size / (1024 * 1024):.2f} MB{RESET}"
                )
            print(f"{TAG_INFO} Output directory: {BOLD}{output_dir_path.resolve()}{RESET}")

            final_path = download_with_progress(
                yt=yt,
                stream=progressive_stream,
                output_dir=output_dir_path,
                description="Downloading",
                filename=f"{safe_title}.mp4",
                colour="magenta",
            )

            print(f"\n{TAG_OK} Download completed!")
            print(f"{TAG_INFO} File saved to: {BOLD}{final_path.resolve()}{RESET}")

    except PytubeFixError as e:
        print(f"{TAG_ERR} YouTube / pytubefix error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{TAG_ERR} Download interrupted by user.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"{TAG_ERR} ffmpeg execution error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{TAG_ERR} Unexpected error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Download a YouTube video in very good quality. "
            "If ffmpeg is available and a higher-resolution adaptive stream exists, "
            "video and audio are downloaded separately (each with a progress bar) "
            "and then merged."
        )
    )
    parser.add_argument(
        "url",
        help="URL of the YouTube video to download",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="downloads",
        help="Output directory (default: ./downloads)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the command-line interface."""
    args = parse_args()
    download_video(args.url, args.output)


if __name__ == "__main__":
    main()
