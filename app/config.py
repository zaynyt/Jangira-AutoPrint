"""Configuration and constants for Jangira AutoPrint"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Application Metadata
APP_NAME = "Jangira AutoPrint"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Cyber Cafe Automatic Printing System"

# Directories
APP_DIR = Path.home() / ".jangira_autoprint"
DB_DIR = APP_DIR / "data"
LOG_DIR = APP_DIR / "logs"
TEMP_DIR = APP_DIR / "temp"
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Ensure directories exist
for directory in [APP_DIR, DB_DIR, LOG_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DB_DIR / "jangira_autoprint.db"

# Logging
LOG_FILE = LOG_DIR / "JangiraAutoPrint.log"
LOG_LEVEL = "INFO"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# PDF Processing
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_PAGES = 300
MAX_COPIES = 99
MIN_COPIES = 1

# Printing
DEFAULT_PRINTER = "Brother DCP-L2520D series"
PRINTER_POLL_INTERVAL = 2  # seconds
PRINT_TIMEOUT = 300  # seconds
JOB_RETRY_LIMIT = 3

# UI
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
ANIMATION_DURATION = 300  # milliseconds

# Status constants
class PrinterStatus:
    READY = "READY"
    PRINTING = "PRINTING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"
    PAUSED = "PAUSED"
    UNKNOWN = "UNKNOWN"

class JobStatus:
    PENDING = "PENDING"
    PRINTING = "PRINTING"
    PRINTED = "PRINTED"
    PRINT_FAILED = "PRINT_FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"

@dataclass
class PrinterConfig:
    """Printer configuration"""
    name: str
    is_default: bool = False
    is_preferred: bool = False

@dataclass
class AppSettings:
    """Application settings"""
    default_printer: str = DEFAULT_PRINTER
    max_file_size: int = MAX_FILE_SIZE
    max_pages: int = MAX_PAGES
    max_copies: int = MAX_COPIES
    auto_start_enabled: bool = False
    polling_interval: int = PRINTER_POLL_INTERVAL
    log_level: str = LOG_LEVEL
    minimize_to_tray: bool = True

# Temporary file cleanup
TEMP_FILE_EXTENSION = ".pdf"
TEMP_RENDER_PREFIX = "jangira_render_"
