#!/usr/bin/env python3
"""Entry point for Jangira AutoPrint application"""

import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.main import main

if __name__ == "__main__":
    main()
