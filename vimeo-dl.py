#!/usr/bin/env python3

import subprocess
import sys

def get_input(prompt):
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)

def main():
    print("📥 Vimeo Embed Downloader (Optimized with aria2c)\n")

    # Get Vimeo iframe URL
    vimeo_url = get_input("🔗 Enter Vimeo player URL (e.g., https://player.vimeo.com/video/.........):\n> ")
    if "player.vimeo.com" not in vimeo_url:
        print("❌ This doesn't look like a Vimeo player URL.")
        sys.exit(1)

    # Get Referer (embed page)
    referer_url = get_input("🌐 Enter the page URL where the video is embedded (the page you watch it on):\n> ")

    # Browser choice
    browser = get_input("🟣 Browser to extract cookies from [default: chrome]:\n> ") or "chrome"

    # Confirm summary
    print("\n=== Download Settings ===")
    print(f"🎥 Vimeo URL     : {vimeo_url}")
    print(f"🌍 Embed Referer : {referer_url}")
    print(f"🟣 Browser       : {browser}")
    print("=========================\n")

    # yt-dlp command with aria2 acceleration
    command = [
        "yt-dlp",
        "--cookies-from-browser", browser,
        "--referer", referer_url,
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--downloader", "aria2c",
        "--downloader-args", "aria2c:-x16 -s16 -k1M",
        vimeo_url
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print("❌ Download failed. Make sure you are logged into Vimeo in your browser.")
        sys.exit(1)

    print("✅ Download + merge completed successfully!")

if __name__ == "__main__":
    main()