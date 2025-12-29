# YouTube Downloader

Small command‑line utility to download a YouTube video in the best possible
quality.

The script automatically decides whether to download:

- **High‑quality adaptive mode** (video‑only + audio‑only + `ffmpeg` merge), or  
- **Progressive mode** (single file containing video + audio),

depending on what streams are available and whether `ffmpeg` is installed.

---

## Features

- Download **YouTube videos** from a URL.
- Automatically choose the **best available quality**:
  - If possible: video‑only stream (highest resolution) + audio‑only stream, then merge with `ffmpeg`.
  - Otherwise: best progressive stream (video + audio in one file).
- **Colored, pip‑style progress bars** using `tqdm`:
  - Separate bars for video and audio in high‑quality mode.
  - Shows bytes downloaded, total size, download speed, and elapsed time.
- Output filename based on the **video title**, sanitized for the filesystem.
- Simple command‑line interface, easy to integrate into other scripts.

---

## Project Structure

Typical minimal project layout:

```text
your-project/
├─ yt_downloader.py
├─ requirements.txt
└─ README.md
```

- `yt_downloader.py` — main script (CLI).
- `requirements.txt` — Python dependencies.
- `README.md` — this documentation.

---

## Requirements

- **Python** 3.8+ (recommended)
- **Python packages** (installed via `pip`):
  - `pytubefix`
  - `tqdm`
- **Optional but recommended**:
  - `ffmpeg` available on your system `PATH`
    - Required for the high‑quality adaptive mode (video+audio merge).

> [!NOTE]
> If `ffmpeg` is missing, the script will still work in **progressive mode**
> (single file, possibly lower resolution).

---

## Installation

### 1. Get the script

Create a folder and place the script file inside, for example:

```bash
mkdir youtube_downloader
cd youtube_downloader
# Put yt_downloader.py here
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
# On Unix/macOS
source .venv/bin/activate
# On Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

You should see something like `(.venv)` at the beginning of your shell prompt.

### 3. Create `requirements.txt` and install dependencies

Put the following content in `requirements.txt`:

```txt
pytubefix
tqdm
```

Then install:

```bash
pip install -r requirements.txt
```

### 4. Install `ffmpeg` (optional but _highly_ recommended)

Install `ffmpeg` using your OS package manager or from the official website:

- **macOS (Homebrew)**  
  ```bash
  brew install ffmpeg
  ```

- **Ubuntu / Debian**  
  ```bash
  sudo apt update
  sudo apt install ffmpeg
  ```

- **Windows (Chocolatey)**  
  ```bash
  choco install ffmpeg
  ```

Or download the official binaries, extract them, and add the `ffmpeg` binary
directory to your system `PATH`.

---

## Usage

From the directory containing `yt_downloader.py`:

```bash
python yt_downloader.py "YOUTUBE_VIDEO_URL"
```

Example:

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Change the output directory

By default, videos are saved into a `downloads/` folder in the current directory.

You can change the output directory with `-o` or `--output`:

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "./my_videos"
```

The output directory will be created automatically if it does not exist.

---

## Command‑Line Options

```text
usage: yt_downloader.py [-h] [-o OUTPUT] url

Download a YouTube video in very good quality. If ffmpeg is available and a
higher-resolution adaptive stream exists, video and audio are downloaded
separately (each with a progress bar) and then merged.

positional arguments:
  url                   URL of the YouTube video to download

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory (default: ./downloads)
```

---

## How It Works (Internals)

### 1. Fetch video information

The script uses `pytubefix.YouTube` to:

- Fetch basic metadata (title, length, etc.).
- Retrieve available streams:
  - **Progressive streams** (`progressive=True`): contain **video + audio**.
  - **Adaptive video‑only streams** (`only_video=True`): **video without audio**.
  - **Adaptive audio‑only streams** (`only_audio=True`): **audio without video**.

### 2. Choose the best streams

The script selects:

1. The **best progressive stream**  
   (highest resolution, MP4 if possible).

2. The **best adaptive video‑only stream**  
   (highest resolution, MP4).

3. The **best adaptive audio‑only stream**  
   (highest bitrate).

Then the logic is:

- If:
  - `ffmpeg` **is available**, and  
  - the best adaptive video‑only stream has **higher resolution** than the best progressive stream  
- Then:
  - Use **high‑quality adaptive mode**:
    - Download video‑only + audio‑only separately (two progress bars).
    - Merge them with `ffmpeg -c copy` into a final `.mp4` file (no re‑encoding).
- Else:
  - Use **progressive mode**:
    - Download the best progressive stream (single file) with one progress bar.

### 3. Progress bars and colors

The script uses `tqdm` with a custom bar format similar to `pip`:

- Shows:
  - Percentage
  - Downloaded bytes
  - Total bytes
  - Download speed
  - Elapsed time
- Separate bars for:
  - Video (high‑quality mode)
  - Audio (high‑quality mode)
  - Progressive (fallback mode)

Colors are implemented with **ANSI escape codes** (no external color library):

- Info messages: typically cyan.
- Success messages: green.
- Warnings: yellow.
- Errors: red.
- Progress bars use a configured color (e.g. green for video, cyan for audio,
  magenta for progressive).

> [!NOTE]
> Some terminals may not support ANSI colors; in that case you may see
> raw codes like `\033[92m`. You can remove or adjust them if needed.

### 4. File naming and paths

- The video title is sanitized to be safe for most filesystems:
  - Forbidden characters like `\ / : * ? " < > |` are replaced.
  - Leading/trailing spaces are removed.
  - Length is limited to avoid very long filenames.
- Output directory:
  - Defaults to `./downloads`.
  - Created automatically if it does not exist.

---

## Examples

### Example 1 — High‑quality mode (with `ffmpeg` and good adaptive streams)

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=EXAMPLE"
```

Typical log (colors not shown here):

```text
[+] Fetching video info…
[+] Title: My Awesome Video
[+] Best progressive stream: 720p
[+] Best adaptive video-only stream: 2160p
[+] ffmpeg available: True

[+] Using high-quality adaptive mode (video + audio + ffmpeg merge).
[+] Video size: 350.54 MB
Downloading video:  34%|███████▎              120M/350M  3.0MB/s  00:40
[+] Audio size: 19.84 MB
Downloading audio:  73%|██████████████▍       14.5M/19.8M 1.8MB/s  00:08

[+] Merging video and audio with ffmpeg into: My Awesome Video.mp4

[✓] Download and merge completed!
[+] Final file: /path/to/downloads/My Awesome Video.mp4
```

### Example 2 — Progressive mode (no `ffmpeg`, or no better adaptive stream)

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=EXAMPLE"
```

Typical log:

```text
[+] Fetching video info…
[+] Title: Another Video
[+] Best progressive stream: 1080p
[+] Best adaptive video-only stream: 1080p
[+] ffmpeg available: False

[!] Using progressive mode (single file: video + audio).
[+] Resolution: 1080p
[+] Size: 120.34 MB
[+] Output directory: /path/to/downloads

Downloading:  58%|█████████▊       70M/120M  4.2MB/s  00:18

[✓] Download completed!
[+] File saved to: /path/to/downloads/Another Video.mp4
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'pytubefix' (or 'tqdm')`

You probably forgot to install dependencies.

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install pytubefix tqdm
```

---

### `ffmpeg` not found / merge errors

- Make sure `ffmpeg` is installed and available in your system `PATH`.
- Try running:

  ```bash
  ffmpeg -version
  ```

  If the command is not found, install `ffmpeg` (see the **Installation** section).

If you do not need high‑quality adaptive mode, you can still use progressive
mode by simply not installing `ffmpeg`.

---

### Colors look broken (weird characters)

If your terminal does not support ANSI color codes, you might see sequences
such as `\033[92m` in the output.

---

### Download fails for some videos

Possible reasons:

- Video is age‑restricted or requires login.
- Video is private or region‑locked.
- Temporary network or YouTube‑side issues.

You can try:

- Running the script again later.
- Using a VPN (if allowed in your jurisdiction).
- Testing with several different videos to confirm the script works.

---

## Extending the Script

You can easily extend the script to:

- Add a `--no-color` option to disable colored output.
- Add an option to **choose a specific resolution** (e.g. force 720p).
- Add **playlist** support:
  - Pass a playlist URL and iterate over its entries.
- Integrate the functions into another Python project:
  - Import `download_video` from `yt_downloader.py` and call it directly.

---

## Legal Note

> [!IMPORTANT]
> This script is provided for **personal use only**.

- Make sure you respect **YouTube’s Terms of Service**.
- Only download content for which you have the **rights** or **explicit
  permission** from the copyright holder.
- The author of the script and this documentation assumes **no responsibility**
  for any misuse.
