"""Build the paper PDF with IEEE reference numbers.

Run from the repo root:  python -B docs/paper/build/build_numbered.py
Step 1: number_refs.py writes build/PAPER_numbered.md (citations renumbered, reference list filled in).
Step 2: build_paper.py builds paper_draft.pdf from that copy instead of PAPER.md.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import number_refs

number_refs.main()

import paperlib as lib

lib.PAPER = HERE / "PAPER_numbered.md"

import build_paper

build_paper.main()
