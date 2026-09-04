# Heart-only Emoji Pack

The editable package contains four registered emoji:

- `01-heart`
- `02-heart-double`
- `03-heart-open`
- `27-ira-heart`

Build and synchronize all generated outputs with:

```bash
python3 pack.py release
```

For validation without release synchronization, run:

```bash
python3 validate_animated.py
python3 validate_tgs.py
python3 -m pytest -q
```
