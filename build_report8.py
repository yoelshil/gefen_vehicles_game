"""
Build report_8.pptx from report_7.pptx by:
  1. Removing the duplicate Slide 8 ("Before" working artifact)
  2. Replacing placeholder images with individual subfigure panels
  3. Filling "Fill" placeholders with real statistics from the analysis CSV

Usage:
  python build_report8.py --input report_7.pptx --output report_8.pptx \
      [--subfigures ./subfigures/] \
      [--stats ./OneShot_N30_ResultsSummary_*.csv]

All flags are optional except --input. If --subfigures is omitted, images are
left as-is. If --stats is omitted, "Fill" placeholders remain.
"""

import argparse
import glob
import os
import sys
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Emu


# ── Helpers ──────────────────────────────────────────────────────────────────

def remove_slide(prs, slide_index):
    sldIdLst = prs.slides._sldIdLst
    sldId = sldIdLst[slide_index]
    rId = sldId.get(qn("r:id"))
    prs.part.drop_rel(rId)
    sldIdLst.remove(sldId)


def find_pictures(slide):
    pics = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            pics.append(shape)
    return pics


def replace_picture(slide, old_shape, image_path):
    left, top, width, height = old_shape.left, old_shape.top, old_shape.width, old_shape.height
    old_shape._element.getparent().remove(old_shape._element)
    slide.shapes.add_picture(str(image_path), left, top, width, height)


def add_picture(slide, image_path, left, top, width, height):
    slide.shapes.add_picture(str(image_path), left, top, width, height)


def find_panel_file(subfig_dir, fig_name, panel_id):
    """Glob for a subfigure PNG: {fig_name}_{panel_id}_*.png"""
    panel_id_fs = panel_id.replace(".", "_")
    pattern = os.path.join(subfig_dir, f"{fig_name}_{panel_id_fs}_*.png")
    matches = sorted(glob.glob(pattern))
    if matches:
        return matches[-1]  # latest by timestamp
    pattern2 = os.path.join(subfig_dir, f"{fig_name}_{panel_id_fs}.png")
    matches2 = sorted(glob.glob(pattern2))
    return matches2[-1] if matches2 else None


def set_cell_text(table, row_idx, col_idx, text):
    cell = table.cell(row_idx, col_idx)
    para = cell.text_frame.paragraphs[0]
    if para.runs:
        para.runs[0].text = text
        for r in list(para.runs[1:]):
            para._p.remove(r._r)
    else:
        para.text = text


def find_table(slide):
    for s in slide.shapes:
        if s.has_table:
            return s.table
    return None


def find_shape_by_text(slide, substring):
    for s in slide.shapes:
        if s.has_text_frame and substring in s.text:
            return s
    return None


def replace_run_text(shape, old_substr, new_text):
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if old_substr in run.text:
                run.text = run.text.replace(old_substr, new_text)
                return True
    return False


def add_paragraph_clone(shape, text, ref_para_idx=-1):
    txBody = shape.text_frame._txBody
    paras = txBody.findall(qn("a:p"))
    ref = None
    for p in reversed(paras):
        if p.findall(qn("a:r")):
            ref = p
            break
    if ref is None:
        ref = paras[ref_para_idx]
    new_p = deepcopy(ref)
    runs = new_p.findall(qn("a:r"))
    if runs:
        for t in runs[0].iter(qn("a:t")):
            t.text = text
            break
        for r in runs[1:]:
            new_p.remove(r)
    ref.addnext(new_p)


# ── Statistics loader ────────────────────────────────────────────────────────

def load_stats(csv_path):
    """Parse ResultsSummary CSV into a dict keyed by question label prefix."""
    import csv
    stats = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row.get("Question", "")
            stats[q] = row
    return stats


def extract_bt1(stats):
    """Extract Blind-to-T1 statistics."""
    for key, row in stats.items():
        if "blind" in key.lower() and "t1" in key.lower():
            return {
                "stat": row.get("Statistic", ""),
                "p": row.get("p_value", ""),
                "sig": row.get("Significance", ""),
                "effect": row.get("Effect_Size", ""),
                "direction": row.get("Values", ""),
            }
    return None


def extract_it2(stats):
    """Extract Icon-to-T2 statistics."""
    for key, row in stats.items():
        if "icon" in key.lower() and "t2" in key.lower():
            return {
                "stat": row.get("Statistic", ""),
                "p": row.get("p_value", ""),
                "sig": row.get("Significance", ""),
                "effect": row.get("Effect_Size", ""),
                "direction": row.get("Values", ""),
            }
    return None


def fmt_sig(p_str):
    """Format p-value string with n.s. or star notation."""
    try:
        p = float(p_str.lstrip("<>= ").replace("< ", ""))
        if p >= 0.05:
            return f"p={p_str} n.s."
        return f"p={p_str}"
    except (ValueError, AttributeError):
        return f"p={p_str}" if p_str else "Fill"


def fmt_answer(direction_str, sig_str):
    """Auto-generate answer from direction counts and significance."""
    try:
        p = float(sig_str.lstrip("<>= ").replace("< ", ""))
        is_sig = p < 0.05
    except (ValueError, AttributeError):
        is_sig = False
    if is_sig:
        return f"Significant; {direction_str}" if direction_str else "Significant"
    return f"Not significant; {direction_str}" if direction_str else "Not significant"


# ── Subfigure placement configuration ────────────────────────────────────────

# Each entry: (old_slide_index_before_removal, shape_name_or_order, fig_name, panel_id)
# After removing slide 8 (idx 7), indices shift for slides >= 8.
# We work on OLD indices first (before removal), then remove the slide.
# Actually, we remove first then work on new indices.

# Mapping: new_slide_index -> [(picture_identifier, fig_name, panel_id)]
# picture_identifier: shape name or positional index among Picture shapes
SUBFIGURE_MAP = {
    # New slide 7 (old 7): Prior (P1-P2) — Fig 2.2 (left) + Fig 2.6 (right)
    6: [
        ("Picture 7", "Fig2", "2_2"),   # left image
        ("Picture 6", "Fig2", "2_6"),   # right image (was labeled 2.9, now 2.6)
    ],
    # New slide 9 (old 10): Classification Results — Fig 2.3 (left) + Fig 9.4 (right)
    8: [
        ("Picture 7", "Fig2", "2_3"),   # left image
        ("Picture 11", "Fig9", "9_4"),  # right image
    ],
    # New slide 10 (old 11): Icon Prior — currently one wide image for Fig 2.4/2.5
    9: [
        ("Picture 5", "Fig2", "2_4"),   # will be split: left half for 2.4
        (None, "Fig2", "2_5"),          # None = add new image for right half
    ],
    # New slide 11 (old 12): First Exposure — Fig 3.1
    10: [
        ("Picture 5", "Fig3", "3_1"),
    ],
    # New slide 12 (old 13): T1-T2 + Overall — Fig 3.2, 3.2b, 3.4
    11: [
        ("Picture 8", "Fig3", "3_2"),   # left
        (None, "Fig3", "3_2b"),         # new: 3.2b near 3.2
        ("Picture 9", "Fig3", "3_4"),   # right
    ],
}


def place_subfigures(prs, subfig_dir):
    """Replace/add subfigure images on content slides."""
    placed = 0
    skipped = 0

    for slide_idx, panel_list in SUBFIGURE_MAP.items():
        slide = prs.slides[slide_idx]
        pictures = {s.name: s for s in slide.shapes if s.shape_type == 13}

        for entry in panel_list:
            shape_name, fig_name, panel_id = entry
            img = find_panel_file(subfig_dir, fig_name, panel_id)

            if img is None:
                print(f"  SKIP: {fig_name} panel {panel_id} — file not found in {subfig_dir}")
                skipped += 1
                continue

            if shape_name is not None and shape_name in pictures:
                old_shape = pictures[shape_name]
                replace_picture(slide, old_shape, img)
                print(f"  Slide {slide_idx+1}: replaced {shape_name} with {os.path.basename(img)}")
                placed += 1
            elif shape_name is None:
                # Add new image — compute position based on slide context
                if slide_idx == 9:
                    # Slide 10 (Icon Prior): split the wide image area into left/right
                    # Original wide image: left=419100, top=1889500, w=11674576, h=4597400
                    half_w = 11674576 // 2
                    left = 419100 + half_w
                    top = 1889500
                    add_picture(slide, img, left, top, half_w, 4597400)
                elif slide_idx == 11:
                    # Slide 12: place 3.2b between 3.2 and 3.4
                    # 3.2 at (1629727, 3472815, 3324225, 3019425)
                    # 3.4 at (7370536, 2920505, 4059463, 3937496)
                    left = 4953952  # between 3.2 right edge and 3.4 left
                    top = 3472815
                    width = 2416584
                    height = 3019425
                    add_picture(slide, img, left, top, width, height)
                else:
                    print(f"  SKIP: no position logic for new image on slide {slide_idx+1}")
                    skipped += 1
                    continue
                print(f"  Slide {slide_idx+1}: added {os.path.basename(img)} (new)")
                placed += 1
            else:
                # Shape name given but not found — try by position order
                pic_list = find_pictures(slide)
                for pic in pic_list:
                    replace_picture(slide, pic, img)
                    print(f"  Slide {slide_idx+1}: replaced {pic.name} (fallback) with {os.path.basename(img)}")
                    placed += 1
                    break
                else:
                    print(f"  SKIP: shape '{shape_name}' not found on slide {slide_idx+1}")
                    skipped += 1

    return placed, skipped


def fill_statistics(prs, stats):
    """Fill all 'Fill' placeholders with real statistics."""
    bt1 = extract_bt1(stats)
    it2 = extract_it2(stats)
    filled = 0

    # ── Slide 5 (idx 4): P2c row (row 4) ──
    tbl5 = find_table(prs.slides[4])
    if tbl5 and bt1:
        set_cell_text(tbl5, 4, 4, bt1["stat"])       # Metric
        set_cell_text(tbl5, 4, 5, fmt_sig(bt1["p"]))  # Sig
        set_cell_text(tbl5, 4, 6, bt1["effect"])       # Effect
        set_cell_text(tbl5, 4, 7, fmt_answer(bt1["direction"], bt1["p"]))  # Answer
        print(f"  Slide 5: P2c row filled with BT1 stats")
        filled += 1

    # ── Slide 6 (idx 5): S3 row (row 6) ──
    tbl6 = find_table(prs.slides[5])
    if tbl6 and it2:
        set_cell_text(tbl6, 6, 4, it2["stat"])       # Metric
        set_cell_text(tbl6, 6, 5, fmt_sig(it2["p"]))  # Sig
        set_cell_text(tbl6, 6, 6, it2["effect"])       # Effect
        set_cell_text(tbl6, 6, 7, fmt_answer(it2["direction"], it2["p"]))  # Answer
        print(f"  Slide 6: S3 row filled with IT2 stats")
        filled += 1

    # ── Slide 10 (idx 9): stat line for BT1 ──
    if bt1:
        shape10 = find_shape_by_text(prs.slides[9], "Blind to T1")
        if shape10:
            eff = bt1['effect']
            eff_str = eff if eff.startswith("d=") else f"d={eff}"
            old = "Blind to T1 (combined effect): Fill diff, Fill p, Fill Cliff's d from v25."
            new = f"Blind to T1 (combined effect): {bt1['stat']}, {fmt_sig(bt1['p'])}, {eff_str}."
            if not replace_run_text(shape10, old, new):
                replace_run_text(shape10, "Fill diff, Fill p, Fill Cliff",
                                 f"{bt1['stat']}, {fmt_sig(bt1['p'])}, {eff_str}")
            print(f"  Slide 10: BT1 stat line filled")
            filled += 1

    # ── Slide 12 (idx 11): stat line for IT2 ──
    if it2:
        shape12 = find_shape_by_text(prs.slides[11], "Icon to T2")
        if shape12:
            eff = it2['effect']
            eff_str = eff if eff.startswith("d=") else f"d={eff}"
            old = "Icon to T2 (exposure learning): Fill diff, Fill p, Fill Cliff's d from v25."
            new = f"Icon to T2 (exposure learning): {it2['stat']}, {fmt_sig(it2['p'])}, {eff_str}."
            if not replace_run_text(shape12, old, new):
                replace_run_text(shape12, "Fill diff, Fill p, Fill Cliff",
                                 f"{it2['stat']}, {fmt_sig(it2['p'])}, {eff_str}")
            print(f"  Slide 12: IT2 stat line filled")
            filled += 1

    # ── Slide 13 (idx 12): summary table last row ──
    tbl13 = find_table(prs.slides[12])
    if tbl13 and it2:
        last_row = len(tbl13.rows) - 1
        set_cell_text(tbl13, last_row, 0, "Icon to T2 (exposure learning)")
        eff = it2['effect']
        eff_str = eff if eff.startswith("d=") else f"d={eff}"
        set_cell_text(tbl13, last_row, 1, f"{it2['stat']}, {fmt_sig(it2['p'])}, {eff_str}")
        sig_text = "Significant" if it2["sig"] and "*" in it2["sig"] else "Not significant"
        set_cell_text(tbl13, last_row, 2, f"{sig_text}; exposure learning from icon baseline")
        print(f"  Slide 13: IT2 summary row filled")
        filled += 1

    return filled


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build report_8.pptx from report_7.pptx")
    parser.add_argument("--input", required=True, help="Path to report_7.pptx")
    parser.add_argument("--output", default="report_8.pptx", help="Output path (default: report_8.pptx)")
    parser.add_argument("--subfigures", default=None, help="Directory with subfigure PNGs from analysis")
    parser.add_argument("--stats", default=None, help="Path to ResultsSummary CSV from analysis")
    parser.add_argument("--keep-slide8", action="store_true", help="Don't remove the duplicate slide 8")
    args = parser.parse_args()

    prs = Presentation(args.input)
    print(f"Loaded {args.input}: {len(prs.slides)} slides")

    # Step 1: Remove duplicate slide 8 (old index 7)
    if not args.keep_slide8:
        slide8 = prs.slides[7]
        slide8_text = ""
        for s in slide8.shapes:
            if s.has_text_frame:
                slide8_text += s.text
        if "Before" in slide8_text or len(prs.slides) == 14:
            remove_slide(prs, 7)
            print(f"Removed slide 8 (duplicate 'Before' slide) → {len(prs.slides)} slides")
        else:
            print("Slide 8 doesn't look like the expected duplicate — keeping it. Use --keep-slide8 to suppress this check.")

    # Step 2: Update figure label "Fig 2.9" → "Fig 2.6" on slide 7 (new idx 6)
    slide7 = prs.slides[6]
    for s in slide7.shapes:
        if s.has_text_frame:
            for para in s.text_frame.paragraphs:
                for run in para.runs:
                    if "2.9" in run.text:
                        run.text = run.text.replace("2.9", "2.6")
                        print(f"  Slide 7: updated label '{run.text}'")

    # Step 3: Place subfigures
    if args.subfigures and os.path.isdir(args.subfigures):
        print(f"\nPlacing subfigures from {args.subfigures}:")
        placed, skipped = place_subfigures(prs, args.subfigures)
        print(f"  → {placed} placed, {skipped} skipped")
    elif args.subfigures:
        print(f"WARNING: subfigures directory not found: {args.subfigures}")
    else:
        print("No --subfigures provided; images unchanged.")

    # Step 4: Fill statistics
    if args.stats and os.path.isfile(args.stats):
        print(f"\nFilling statistics from {args.stats}:")
        stats = load_stats(args.stats)
        filled = fill_statistics(prs, stats)
        print(f"  → {filled} sections filled")
    elif args.stats:
        print(f"WARNING: stats file not found: {args.stats}")
    else:
        print("No --stats provided; 'Fill' placeholders unchanged.")

    # Step 5: Save
    prs.save(args.output)
    print(f"\nSaved to {args.output} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
