# Editing Guide

1. Edit one canonical source in `04-editable-project/frame_motions`.
2. Run `python3 pack.py release` from `04-editable-project`.
3. Run `python3 validate_animated.py`, `python3 validate_tgs.py`, and
   `python3 -m pytest -q`.

Release directories are generated; do not edit them manually.
