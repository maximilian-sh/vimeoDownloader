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
- 🖥️ Simple terminal interface

## 🛠️ Requirements

- Python >= 3.7
- yt-dlp
- aria2c
- A working browser session (Chrome recommended)

## 🚀 Setup Guide

### 1. Install yt-dlp
```bash
pip install -U yt-dlp
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
2. Make it executable (optional):
```bash
chmod +x vimeo-dl.py
```

## 💻 Usage Guide

Simply run:
```bash
./vimeo-dl.py
```

The script will prompt you for:
1. The Vimeo player URL (from the iframe)
2. The page URL where the video is embedded
3. Your browser choice (default: chrome)

## 📝 Example

```bash
📥 Vimeo Embed Downloader (Optimized with aria2c)

🔗 Enter Vimeo player URL:
> https://player.vimeo.com/video/123456789

🌐 Enter the page URL where the video is embedded:
> https://example.com/video-page

🟣 Browser to extract cookies from [default: chrome]:
> 

🎯 Downloading: https://player.vimeo.com/video/123456789
🌐 Using referer: https://example.com/video-page
🟣 Cookies from browser: chrome
...
✅ Download + merge completed successfully!
```

## 💡 Tips & Notes

### Important Notes
- Ensure you're logged into the platform in your browser before downloading
- First-time users may need to confirm yt-dlp's browser cookie access
- Downloaded MP4s appear in the script's directory

### Browser Support
- Works with Chrome (default)
- Also supports Brave, Edge, and Chromium
- Simply type the browser name when prompted

### Future Enhancements
- Create a proper .app for double-click launching
- Add Automator workflow support for Mac
- Add custom ASCII art and colorized CLI outputs
- Implement fancy emoji menus

---

<div align="center">
  Made with ❤️ for Vimeo Video Downloads
</div>