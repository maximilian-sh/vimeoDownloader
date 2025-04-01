# 🎥 Vimeo Downloader (Private Embed Optimized)

> A powerful tool for downloading private Vimeo videos from embed-only sources, optimized for speed and reliability.

## 📑 Table of Contents
- [Features](#-features)
- [Requirements](#-requirements)
- [Setup Guide](#-setup-guide)
- [Usage Guide](#-usage-guide)
- [Example](#-example)
- [Tips & Notes](#-tips--notes)

## ✨ Features

- 🎯 Supports **embed-only** Vimeo videos
- 🔐 Uses your **logged-in browser session** automatically
- 🔒 Supports **referer-locked** videos
- 📥 Downloads **best video + best audio** streams
- 🎬 Merges into clean **MP4** format
- ⚡ Accelerated using **aria2c** (up to 16x faster)
- 📊 Real-time download progress tracking
- 🗂️ Organized downloads in dedicated folder
- 🧹 Automatic cleanup of temporary files
- 🖥️ Interactive browser selection menu

## 🛠️ Requirements

- Python >= 3.7
- yt-dlp
- aria2c
- questionary (Python package)
- A working browser session (Chrome recommended)

## 🚀 Setup Guide

### 1. Install Python Dependencies
```bash
pip install -U yt-dlp questionary
```

### 2. Install aria2c

**macOS:**
```bash
brew install aria2
```

**Ubuntu/Debian:**
```bash
sudo apt install aria2
```

### 3. Download the Script
1. Save `vimeo-dl.py` to your preferred location
2. Make it executable:
```bash
chmod +x vimeo-dl.py
```

## 💻 Usage Guide

Simply run:
```bash
./vimeo-dl.py
```

The script will:
1. Check for required dependencies
2. Present an interactive browser selection menu
3. Prompt for the Vimeo player URL
4. Ask for the page URL where the video is embedded
5. Show download progress in real-time
6. Save the video to `~/Downloads/vimeo_downloads/`

## 📝 Example

```bash
Vimeo Downloader
==================================================

Enter Vimeo player URL:
> https://player.vimeo.com/video/123456789

Enter the page URL where the video is embedded:
> https://example.com/video-page

Select browser for cookie extraction:
  > chrome
    firefox
    edge
    brave
    chromium
    safari

Download Configuration:
Video URL: https://player.vimeo.com/video/123456789
Referer:   https://example.com/video-page
Browser:   chrome
Output Directory: /Users/username/Downloads/vimeo_downloads
==================================================

Starting download...
[download] Downloading video ...
[download] Downloading audio ...
[download] Merging formats ...
Download completed successfully.
```

## 💡 Tips & Notes

### Important Notes
- Ensure you're logged into the platform in your browser before downloading
- First-time users may need to confirm yt-dlp's browser cookie access
- Downloaded videos appear in `~/Downloads/vimeo_downloads/`
- Temporary files are automatically cleaned up

### Browser Support
- Interactive selection menu for supported browsers
- Chrome (default)
- Firefox
- Edge
- Brave
- Chromium
- Safari

### Features
- Real-time progress tracking
- Automatic file organization
- Clean temporary file management
- Error handling and validation
- User-friendly interface

---

<div align="center">
  Made with ❤️ for Vimeo Video Downloads
</div>