"""
ARAN test configuration.
Adds backend/ to sys.path so all backend modules resolve correctly.
"""
import sys
import os

# Allow tests to import backend modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
