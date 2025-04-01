#!/usr/bin/env python3

import sys
import os
import logging
import subprocess
import shutil
import tempfile
import re
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

def clean_progress_output(line: str) -> Optional[str]:
    """Clean and format progress output."""
    # Extract download progress information
    if '[download]' in line and '%' in line:
        return line.strip()
    
    # Extract aria2c progress
    if '[DL:' in line:
        # Extract download speed
        dl_match = re.search(r'\[DL:([\d.]+)MiB\]', line)
        if dl_match:
            speed = float(dl_match.group(1))
            
            # Find any percentage in the line
            percent_match = re.search(r'(\d+)%', line)
            percent = percent_match.group(1) if percent_match else ""
            
            if percent:
                return f"Downloading... {speed:.1f} MiB/s ({percent}%)"
            else:
                return f"Downloading... {speed:.1f} MiB/s"
    
    # Show merging status
    if '[Merger]' in line:
        return "Merging video and audio..."
    
    # Show moving status
    if '[MoveFiles]' in line:
        return "Moving file to downloads folder..."
        
    return None

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

    def get_browser(self) -> str:
        """Get browser selection from user."""
        return questionary.select(
            "Select browser for cookie extraction:",
            choices=self.SUPPORTED_BROWSERS,
            default='chrome',
            style=self.style
        ).ask()

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

    def download(self, vimeo_url: str, referer_url: str, browser: str) -> None:
        """Execute the download using yt-dlp with aria2c."""
        command = [
            "yt-dlp",
            "--cookies-from-browser", browser,
            "--referer", referer_url,
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--downloader", "aria2c",
            "--downloader-args", "aria2c:-x16 -s16 -k1M",
            "--paths", f"temp:{self.temp_dir}",
            "--paths", f"home:{self.downloads_dir}",
            "--progress",
            "--newline",
            vimeo_url
        ]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            last_progress = ""
            # Process output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Clean and format the progress output
                    progress = clean_progress_output(output)
                    if progress and progress != last_progress:
                        print(progress + ' ' * 20, end='\r')
                        last_progress = progress
            
            # Check for errors
            if process.returncode != 0:
                error = process.stderr.read()
                raise DownloadError(f"Download failed: {error}")
                
        except subprocess.CalledProcessError as e:
            raise DownloadError(f"Download failed: {e.stderr}")

    def run(self) -> None:
        """Main execution flow."""
        try:
            logger.info("Vimeo Downloader")
            logger.info("=" * 50)

            vimeo_url, referer_url = self.get_urls()
            browser = self.get_browser()

            logger.info("\nDownload Configuration:")
            logger.info(f"Video URL: {vimeo_url}")
            logger.info(f"Referer:   {referer_url}")
            logger.info(f"Browser:   {browser}")
            logger.info(f"Output Directory: {self.downloads_dir}")
            logger.info("=" * 50 + "\n")

            logger.info("Starting download...")
            self.download(vimeo_url, referer_url, browser)
            logger.info(f"\nDownload completed successfully.")
            logger.info(f"Video saved in: {self.downloads_dir}")

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