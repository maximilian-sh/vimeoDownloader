#!/usr/bin/env python3

import sys
import os
import logging
import subprocess
import shutil
import tempfile
import re
import time
from pathlib import Path
from typing import Optional
import questionary
from questionary import Style
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class DependencyError(Exception):
    """Raised when a required dependency is missing."""
    pass

class URLError(Exception):
    """Raised when a URL is invalid."""
    pass

class DownloadError(Exception):
    """Raised when download fails."""
    pass

def clean_progress_output(line: str) -> tuple[str, Optional[str]]:
    """Categorize and clean yt-dlp output line (from merged stdout/stderr)."""
    line = line.strip()

    # Priority 1: Standard yt-dlp download progress
    if (
        line.startswith('[download]') and
        '%' in line and
        ('MiB' in line or 'KiB' in line or 'GiB' in line or 'bytes' in line) and
        ' of ' in line  # Ensures it's like "10% of 100MiB"
    ):
        cleaned_progress = line.replace("[download]", "Progress:").strip()
        return "PROGRESS", cleaned_progress

    # Simplified Status lines
    if line.startswith('[vimeo]'):
        if 'Extracting URL:' in line: return "STATUS_INFO", "Extracting info..."
        if 'Downloading webpage' in line: return "STATUS_INFO", "Fetching page..."
        return "IGNORE", None

    if 'Merging formats' in line or ('[ffmpeg]' in line and 'Merging' in line.lower()):
        return "STATUS_MERGE", "Merging streams..."
    
    if line.startswith('[info]') and 'Video title:' in line:
        return "STATUS_INFO", line.replace("[info]", "Info:").strip()
    if line.startswith('[download]') and 'Destination:' in line:
        return "IGNORE", None 
    if line.startswith('[download]') and 'has already been downloaded' in line:
        return "STATUS_INFO", "Video already downloaded. Skipping..."
    if line.startswith('[FixupM3u8]') or line.startswith('[FixupTimestamp]'):
        return "STATUS_INFO", "Finalizing stream..."

    # Catch common error indicators
    if (
        line.lower().startswith('error:') or 
        line.lower().startswith('yt-dlp: error:') or
        (line.startswith('WARNING:') and 'unable to download video data' in line.lower()) or
        (line.startswith('ERROR:') and 'giving up' in line.lower()) # yt-dlp can also just use plain ERROR:
    ):
        return "ERROR_LINE", line

    return "IGNORE", None

class VimeoDownloader:
    SUPPORTED_BROWSERS = [
        'chrome',
        'firefox',
        'edge',
        'brave',
        'chromium',
        'safari'
    ]

    def __init__(self):
        self.check_dependencies()
        self.style = Style([
            ('question', 'bold'),
            ('selected', 'underline'),
            ('pointer', 'bold')
        ])
        self.setup_directories()

    def setup_directories(self) -> None:
        """Setup output and temporary directories."""
        # Create downloads directory in user's home
        self.downloads_dir = Path.home() / 'Downloads' / 'vimeo_downloads'
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix='vimeo_dl_'))
        logger.debug(f"Created temporary directory: {self.temp_dir}")

    def cleanup(self) -> None:
        """Clean up temporary files and directories."""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.debug("Cleaned up temporary directory")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {e}")

    @staticmethod
    def check_dependencies() -> None:
        """Verify all required dependencies are installed."""
        missing = []
        
        # Check yt-dlp
        if not shutil.which('yt-dlp'):
            missing.append('yt-dlp')
        
        # Check aria2c
        if not shutil.which('aria2c'):
            missing.append('aria2c')
        
        if missing:
            raise DependencyError(
                f"Missing required dependencies: {', '.join(missing)}. "
                "Please install them before running this program."
            )

    @staticmethod
    def validate_url(url: str, required_domain: Optional[str] = None) -> bool:
        """Validate URL format and optionally check domain."""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
            if required_domain and required_domain not in result.netloc:
                return False
            return True
        except Exception:
            return False

    def get_urls(self) -> tuple[str, str]:
        """Get and validate Vimeo and referer URLs from user."""
        while True:
            vimeo_url = questionary.text(
                "Enter Vimeo player URL:",
                validate=lambda text: self.validate_url(text, 'player.vimeo.com'),
                style=self.style
            ).ask()

            referer_url = questionary.text(
                "Enter the page URL where the video is embedded:",
                validate=lambda text: self.validate_url(text),
                style=self.style
            ).ask()

            return vimeo_url, referer_url

    def download(self, vimeo_url: str, referer_url: str) -> None:
        """Execute the download using yt-dlp with aria2c, trying all supported browsers."""
        
        download_successful = False
        last_error_message = "Unknown error."

        for browser in self.SUPPORTED_BROWSERS:
            logger.info(f"Trying {browser.capitalize()} browser cookies...")
            command = [
                "yt-dlp",
                "--cookies-from-browser", browser,
                "--referer", referer_url,
                "-f", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                "--downloader", "aria2c",
                "--downloader-args", "aria2c:-x16 -s16 -k1M --console-log-level=warn --show-console-readout=true",
                "--progress",
                "--newline", # Force each progress update to be on a new line from yt-dlp
                "--paths", f"temp:{self.temp_dir}",
                "--paths", f"home:{self.downloads_dir}",
                vimeo_url
            ]

            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, # Merge stderr into stdout
                    text=True,
                    bufsize=1, 
                    universal_newlines=True
                )
                
                spinner_frames = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
                spinner_idx = 0
                spinner_counter = 0  # Add counter to reduce spinner frequency
                PROGRESS_LINE_WIDTH = 80
                last_line_ended_with_cr = False
                displaying_progress = False # New state variable
                
                # logger.info("Starting download...") # Moved to be per-browser attempt

                while True:
                    output_line_raw = process.stdout.readline()

                    if not output_line_raw and process.poll() is not None:
                        break 

                    if output_line_raw:
                        line_type, message = clean_progress_output(output_line_raw)

                        if line_type == "PROGRESS":
                            # Progress always overwrites current line.
                            sys.stdout.write(message.ljust(PROGRESS_LINE_WIDTH) + "\r")
                            last_line_ended_with_cr = True
                            displaying_progress = True # Set overall state
                        elif line_type in ["STATUS_INFO", "STATUS_MERGE", "ERROR_LINE"]:
                            if last_line_ended_with_cr:
                                sys.stdout.write("\n") # Newline if previous was progress/spinner
                            logger.info(message)  # Use logger instead of direct stdout
                            last_line_ended_with_cr = False
                            displaying_progress = False # Reset overall state
                            if line_type == "ERROR_LINE":
                                last_error_message = message 
                        elif line_type == "IGNORE":
                            if not displaying_progress: # Check overall state
                                spinner_counter += 1
                                if spinner_counter % 5 == 0:  # Only update spinner every 5 IGNORE lines
                                    spinner_char = spinner_frames[spinner_idx]
                                    spinner_idx = (spinner_idx + 1) % len(spinner_frames)
                                    sys.stdout.write(f"{spinner_char} Processing...".ljust(PROGRESS_LINE_WIDTH) + "\r")
                                    last_line_ended_with_cr = True
                            # If displaying_progress is true, do nothing for IGNORE lines to keep progress visible
                    
                    sys.stdout.flush()
                    # Removed 'elif process.poll() is None: pass' as it's covered by readline blocking
            
                if last_line_ended_with_cr:
                    sys.stdout.write("\n")
                sys.stdout.flush()

                process.wait() 
                if process.returncode == 0:
                    logger.info(f"✅ Download successful using {browser.capitalize()} browser cookies!")
                    download_successful = True
                    break # Exit browser loop on success
                else:
                    logger.warning(f"❌ {browser.capitalize()} browser failed (exit code {process.returncode})")
                    # last_error_message is already captured by clean_progress_output if it was an ERROR_LINE
                    # If not, we can use a generic message or try to capture more from stderr if it wasn't merged.
                    if "ERROR_LINE" not in last_error_message : # Avoid overwriting specific yt-dlp error
                         last_error_message = f"yt-dlp exited with code {process.returncode} using {browser}."
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ {browser.capitalize()} execution failed: {e.stderr if e.stderr else e}")
                last_error_message = f"Execution failed with {browser}: {e.stderr if e.stderr else e}"
                continue # Try next browser
            except Exception as e:
                logger.error(f"❌ Unexpected error with {browser.capitalize()}: {e}")
                last_error_message = f"Unexpected error with {browser}: {e}"
                continue # Try next browser
        
        if not download_successful:
            raise DownloadError(f"All browser attempts failed. Last known error: {last_error_message}")


    def run(self) -> None:
        """Main execution flow."""
        try:
            logger.info("🎬 Vimeo Downloader")
            logger.info("=" * 50)
            logger.info("Please ensure you are logged into the website where the video is embedded")
            logger.info("in at least one of the following browsers:")
            for browser_name in self.SUPPORTED_BROWSERS:
                logger.info(f"  • {browser_name.capitalize()}")
            logger.info("The script will attempt to use cookies from each to access the video.")
            logger.info("=" * 50) 

            vimeo_url, referer_url = self.get_urls()
            
            logger.info("\nDownload Configuration:") 
            logger.info(f"Video URL: {vimeo_url}")
            logger.info(f"Referer:   {referer_url}")
            logger.info(f"Output Directory: {self.downloads_dir}")
            logger.info("=" * 50)
            logger.info("")  # Add blank line for better readability

            self.download(vimeo_url, referer_url) # Removed browser argument
            logger.info("\n🎉 Download completed successfully!") 
            logger.info(f"📁 Video saved in: {self.downloads_dir}")

        except KeyboardInterrupt:
            logger.info("\nOperation cancelled by user.")
            sys.exit(1)
        except DependencyError as e:
            logger.error(f"Setup Error: {e}")
            sys.exit(1)
        except URLError as e:
            logger.error(f"URL Error: {e}")
            sys.exit(1)
        except DownloadError as e:
            logger.error(f"Download Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            self.cleanup()

def main():
    downloader = VimeoDownloader()
    downloader.run()

if __name__ == "__main__":
    main()