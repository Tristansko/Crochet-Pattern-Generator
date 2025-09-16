# Crochet-Pattern-Generator
A simple crochet pattern generator made in Python. Further feature implementation planned.
# Crochet Pattern Generator — Developer Guide

## Overview
A Tkinter + Matplotlib GUI that converts an input image to a stitch grid for crochet patterns.
It supports multi‑tone quantization (2–10 tones), grayscale or color display, per‑tone custom colors,
keep‑aspect dimension linking, manual/auto padding, guide lines, row numbers, and PNG/PDF export.

## Key Files
- `Crochet_Pattern_Generator.py` — Reference implementation with per‑line comments.

## Features (quick list)
- Multi‑tone quantization (even bins).
- Grayscale **or** color palettes (palette picker).
- Per‑tone custom colors that apply in both modes.
- Linked rows/width when “Keep aspect” is on.
- Manual padding (L/R/T/B) + auto padding (% of min dimension).
- High‑contrast grid + optional thicker guides.
- Row numbering (1 at bottom, N at top).
- Export to PNG/PDF.
- Brightness offset + invert pre‑processing.

## Architecture
```
Tk (root)
└── CrochetPatternApp(Tk)
    ├── State (IntVar/BooleanVar/StringVar): size, tones, color mode, padding, etc.
    ├── _build_ui(): constructs controls + Matplotlib canvas
    ├── _set_traces(): binds IntVar writes to maintain aspect (rows<->cols)
    ├── open_image(): file open + grayscale conversion
    ├── apply_auto_padding(): equal padding by percentage
    ├── _quantize_even(): grayscale→tone indices (0..T-1) via evenly spaced bins
    ├── _make_pattern_array(): resize, center within padding, brightness/invert, quantize
    ├── _get_cmap(): assemble colormap (palette or grayscale), apply custom per‑tone overrides
    ├── _draw_contrast_grid(): imshow + gridlines + guides + legend + row nums
    ├── render(): recompute and redraw
    └── export(): export to PNG/PDF
```

## Data Flow
1. **open_image** → PIL image (grayscale).
2. **render** reads UI state → calls **_make_pattern_array**.
3. **_make_pattern_array** → creates 2D `np.ndarray[int]` of tones (0..T-1), with padding as 0.
4. **_get_cmap** builds a `ListedColormap` based on color mode + overrides.
5. **_draw_contrast_grid** renders array and decorations to the axes/canvas.
6. **export** creates a high‑DPI figure and reuses drawing code for file output.

## Core Concepts
- **Tone indexing**: `0` = darkest; padding uses `0`. Higher index = lighter tone.
- **Gridlines**: dual white/black lines ensure visibility regardless of underlying tone.
- **Linked aspect**: when enabled, changing rows recomputes width (and vice versa) using the source image aspect ratio.
- **Legend**: shows final color mapping (including custom overrides) and tone indices.

## Extending Quantization
Current: **even bins** using `np.linspace + np.digitize`.
Possible upgrades:
- **Histogram/percentile bins**: choose edges so each bin has equal pixel count (balanced tones).
- **K‑means (1D)**: cluster grayscale values into `k` centroids (sklearn or manual Lloyd’s algorithm).
- **Adaptive contrast**: auto set brightness offset from histogram mean/median before quantization.
- **Dithering**: ordered/Bayer or error‑diffusion to improve visual detail at low tone counts.

Where to plug in:
- Replace `_quantize_even` with your method (same signature). Keep output 0..T‑1.

## Colormap Strategy
- When **Use colors** is ON: start from chosen palette → apply per‑tone overrides.
- When OFF: grayscale levels → apply any overrides (so you can color critical tones while staying mostly gray).

## Performance Notes
- Use `Image.NEAREST` to resize for speed and blocky cells.
- Keep canvas size modest for interactivity (e.g., ≤ 250k cells for smooth UI).
- Export uses a fresh high‑DPI figure to keep UI responsive.

## Testing Checklist
- Open various image sizes and aspect ratios.
- Toggle **Keep aspect** then change rows/width; verify correct linkage.
- Try tones = 2, 3, 4, 8, 10 and verify legend + mapping.
- Set custom colors for random tones; toggle color mode; ensure overrides persist.
- Padding: manual values and auto‑padding (%); confirm padding stays tone 0.
- Export PNG/PDF; check gridlines, guides, and labels are crisp.
- Brightness offset and invert: confirm expected changes before quantization.

## Packaging Ideas
- Provide a `requirements.txt` with `Pillow` and `matplotlib`.
- Add a `setup.py` or use `pyproject.toml` for packaging.
- Create a frozen app via `pyinstaller` for one‑click execution.

## Known Limitations
- Even‑bin quantization can under‑utilize contrast on skewed histograms.
- Very large grids (e.g., > 1M cells) may feel slow to render and export.

## Roadmap (suggested)
- Add histogram‑based or k‑means quantization.
- Row‑by‑row stitch counts + CSV/PDF export.
- Save/Load presets (tones, colors, layout).
- Keyboard shortcuts (R/W/T/B for padding fields; +/- tones).
- SVG export for vector workflows.
- Print‑friendly symbol key (ASCII/Unicode symbols per tone).

## FAQ
**Q: Why are my colors not exactly right in grayscale mode?**  
A: Grayscale mode renders gray by default but honors per‑tone custom overrides; only the tones you override become colored.

**Q: How do I keep the image centered with padding?**  
A: The code computes inner area (rows/cols minus padding), resizes to fit, and centers using offsets `off_x/off_y`.

**Q: Can I make the gridlines thicker?**  
A: Increase the widths in `_draw_contrast_grid` and/or reduce alpha on the thin pass.

## License
None
