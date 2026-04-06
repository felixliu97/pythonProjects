#!/usr/bin/env python3
"""
Monopoly Game - Main Entry Point

Run this file to start the graphical Monopoly game.

Usage:
    python run_monopoly.py
"""

import sys
import os

# Add the monopoly package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monopoly.gui import main

if __name__ == "__main__":
    main()
