#!/usr/bin/env python3
"""Add the R04-T048 section to Module04/07.QualcommQNN.md. Run from the repository root:

    python3 work/R04-T048/apply_lesson_section.py

Inserts the section before "Additional Resources" and adds a table-of-contents entry.
Stops with a message (and changes nothing) if the lesson layout differs or the section exists.
"""
import sys
from pathlib import Path

lesson = Path("Module04/07.QualcommQNN.md")
section_file = Path(__file__).resolve().parent / "lesson_section.md"
if not lesson.is_file():
    sys.exit("run this from the repository root (cannot find %s)" % lesson)
section = section_file.read_text(encoding="utf-8").strip() + "\n\n"
text = lesson.read_text(encoding="utf-8")
old_toc = "9. [Additional Resources](#additional-resources)"
new_toc = ("9. [Applied Example: Platform Compatibility Scenario Assessment](#applied-example-platform-compatibility-scenario-assessment)\n"
           "10. [Additional Resources](#additional-resources)")
if "Applied Example: Platform Compatibility Scenario Assessment" in text:
    sys.exit("already added; nothing changed")
if old_toc not in text or "## Additional Resources" not in text:
    sys.exit("lesson layout changed; nothing changed")
text = text.replace(old_toc, new_toc, 1).replace("## Additional Resources", section + "## Additional Resources", 1)
lesson.write_text(text, encoding="utf-8")
print("lesson updated")
