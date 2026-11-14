#!/usr/bin/env python3
"""Add the R04-T049 section to the end of Module02/06.phisilica.md. Run from the repository root:

    python3 work/R04-T049/apply_lesson_section.py

Appends the section after the last line of the lesson. Stops with a message (and changes
nothing) if the section is already there.
"""
import sys
from pathlib import Path

lesson = Path("Module02/06.phisilica.md")
section_file = Path(__file__).resolve().parent / "lesson_section.md"
if not lesson.is_file():
    sys.exit("run this from the repository root (cannot find %s)" % lesson)
section = section_file.read_text(encoding="utf-8").strip() + "\n"
text = lesson.read_text(encoding="utf-8")
if "Applied Example: Platform Compatibility Evaluation Experiment" in text:
    sys.exit("already added; nothing changed")
lesson.write_text(text.rstrip("\n") + "\n\n" + section, encoding="utf-8")
print("lesson updated")
