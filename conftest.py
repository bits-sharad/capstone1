"""
Pytest configuration file.

Ensures the project package is importable when running tests.
"""

import sys
from pathlib import Path

# Add project root (directory containing Project and pytest tests) to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
