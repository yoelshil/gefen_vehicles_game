# Prompt: Auto-Place v_2_4 Subfigures into report_8.pptx

Use this prompt in a separate chat to update `build_report8.py` and create the presentation with the new analysis figures from `oneshot_analysis_v_2_4.py`.

---

## Context

The analysis script `oneshot_analysis_v_2_4.py` generates composite figures (Fig1–Fig10) and optionally saves each subplot panel as a standalone PNG in `subfigures/`. The naming convention is:

```
{FigName}_{panel_id}_{timestamp}.png
```

For example: `Fig2_2_4m_20250601_1200.png`, `Fig10_9_1_20250601_1200.png`

The script `build_report8.py` takes `report_7.pptx`, removes the duplicate slide 8, and replaces placeholder images with the correct subfigure panels. It needs to be updated to reflect the v_2_4 restructuring.

## What changed in v_2_4

### Figure 2 (Prior Characterization) — expanded from 2x3 to 2x4
New panels added:
- **2.4m**: Blind vs Icon estimates, 3-role (rare-mean collapsed) — at grid position [1,1]
- **2.5m**: Estimation shifts, 3-role (rare-mean collapsed) — at grid position [1,3]

Layout:
| [0,0] 2.1 | [0,1] 2.2 | [0,2] 2.3 | [0,3] 2.6 |
| [1,0] 2.4 | [1,1] 2.4m | [1,2] 2.5 | [1,3] 2.5m |

### Figure 3 (Learning) — rearranged within 5x3
- 3.3m moved from [4,0] to [2,2] (next to 3.3)
- Trajectory panels grouped: 3.4→[3,0], 3.5→[3,1], 3.6→[3,2]
- 3.7 moved to [4,0]
- 3.6 no longer shows Bimodal-symmetric (n=1)

Layout:
| [0,0] 3.1 | [0,1] 3.2 | [0,2] 3.2a |
| [1,0] 3.2b | [1,1] 3.2c | [1,2] 3.2d |
| [2,0] 3.2e | [2,1] 3.3 | [2,2] 3.3m |
| [3,0] 3.4 | [3,1] 3.5 | [3,2] 3.6 |
| [4,0] 3.7 | hidden | hidden |

### Figure 4 (Items) — restructured from 4x3 to 3x4
Rare-mean panels paired next to their counterparts:

Layout:
| [0,0] 4.1 | [0,1] 4.1m | [0,2] 4.2 | [0,3] 4.2m |
| [1,0] 4.3 | [1,1] 4.4 | [1,2] 4.5 | [1,3] 4.6 |
| [2,0] 4.7 | [2,1] 4.7m | [2,2] 4.8 | [2,3] 4.9 |

### New Figure 10 (Timing × Item Role) — 2x3 grid
Panels:
- **9.1**: RT vs Dominant Error (scatter, T2)
- **9.2**: RT vs Medium Error (scatter, T2)
- **9.3**: RT vs Rare Error (scatter, T2)
- **9.4**: Role Error by RT Tertile (grouped bar)
- **9.5**: Deliberation vs Role Error (scatter, 3 series)
- **9.6**: RT-Accuracy Summary Table

Note: The function is called `create_figure9()` internally but saved as `Fig10_TimingRole`. Panel titles inside the code use "9.x" numbering.

## Task for the other chat

Update `build_report8.py` to:

1. **Update `SUBFIGURE_MAP`** to include any new panels that should appear in the presentation. Consider adding:
   - 2.4m and 2.5m on the Icon Prior slide (slide 10 / idx 9) alongside 2.4 and 2.5
   - Figure 10 panels on a new slide if one is added to the presentation

2. **Add a new slide** (or slides) to the presentation for:
   - Figure 10 (Timing × Item Role) — at minimum panels 9.4 (Role Error by RT Tertile) and 9.6 (Summary Table)
   - Optionally: rare-mean comparison panels (4.1m, 4.2m, 4.7m) if they're research-relevant for the presentation

3. **Update the panel file patterns** — the new panels use these IDs:
   - `2_4m` → Fig2 panel 2.4m
   - `2_5m` → Fig2 panel 2.5m
   - `3_3m` → Fig3 panel 3.3m
   - `4_1m`, `4_2m`, `4_7m` → Fig4 rare-mean panels
   - `9_1` through `9_6` → Fig10 panels (note: saved as Fig10 but panel titles say 9.x)

4. **Verify the subfigure naming**: Check `save_individual_panels()` in the analysis script to confirm that panel titles (used as file name prefixes) match the expected patterns. The function extracts the first token of `ax.get_title()`, replaces dots with underscores.

## Files involved
- `/home/user/gefen_vehicles_game/build_report8.py` — the script to update
- `/home/user/gefen_vehicles_game/oneshot_analysis_v_2_4.py` — analysis source (reference)
- `report_7.pptx` — input presentation (14 slides, slide 8 is duplicate)

## Slide structure after slide 8 removal (13 slides)

| Idx | Slide | Content | Subfigures |
|-----|-------|---------|------------|
| 0 | 1 | Cover | — |
| 1 | 2 | EXP Design | — |
| 2 | 3 | Research Questions | — |
| 3 | 4 | Prior Table (P1-P6) | — |
| 4 | 5 | Icon Prior Table (P7, P2a, P2b, P2c) | — |
| 5 | 6 | Learning Table (L1-L3, S1-S3) | — |
| 6 | 7 | Prior (P1-P2) | Fig 2.2, Fig 2.6 |
| 7 | 8 | Classification Method | — |
| 8 | 9 | Classification Results (P3-P6) | Fig 2.3, Fig 9.4 |
| 9 | 10 | Icon Prior (P7, P2a, P2b) | Fig 2.4, Fig 2.5, **+2.4m, +2.5m** |
| 10 | 11 | First Exposure (L1-L2) | Fig 3.1 |
| 11 | 12 | T1-T2 + Overall (L3, S1, S2) | Fig 3.2, Fig 3.2b, Fig 3.4 |
| 12 | 13 | Summary | — |
| NEW | 14 | **Timing × Item Role** | Fig10: 9.4, 9.6 (or all 6 panels) |

## How to run

```bash
# First run the analysis to generate subfigures:
python oneshot_analysis_v_2_4.py --save-subfigures

# Then build the report:
python build_report8.py \
  --input report_7.pptx \
  --output report_8.pptx \
  --subfigures ./subfigures/ \
  --stats ./OneShot_N30_ResultsSummary_*.csv
```
