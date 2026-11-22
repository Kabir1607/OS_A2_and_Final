"""Smart Library, Assignment 1 (Python port).

Usage:  python3 main.py INPUT_FILE FCFS|PRIORITY
"""

import sys

from library_sim.a1 import a1_main

if __name__ == "__main__":
    sys.exit(a1_main(sys.argv[1:]))
