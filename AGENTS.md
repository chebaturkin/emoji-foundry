# Chebaturkin Telegram Heart Pack

This project contains exactly four Telegram custom emoji:

1. `01-heart`
2. `02-heart-double`
3. `03-heart-open`
4. `27-ira-heart`

The canonical animation sources are in `04-editable-project/frame_motions`.
Generated files in `01-ready-to-upload`, `02-static-png`, `03-previews`,
`04-editable-project/frames`, `upload`, `tgs_upload`, and `previews` are only
updated through the build and release commands.

Visible elements may use only BLUE `#2E3A4D`, TAUPE `#C4C1B4`, PAPER
`#F2F0E9`, and INK `#0D0D0D`. `27-ira-heart` keeps the word `ИРА` in PAPER,
without an outline.

After a source change, run:

```bash
cd 04-editable-project
python3 pack.py release
python3 validate_animated.py
python3 validate_tgs.py
python3 -m pytest -q
```

Update `SHA256SUMS` through `python3 pack.py release`; do not edit it by hand.
