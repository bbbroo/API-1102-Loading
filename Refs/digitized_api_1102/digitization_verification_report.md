# API RP 1102 Digitization Verification Report

## Scope

Digitized API RP 1102, Seventh Edition graph-derived factors for Figures 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18-A, and 18-B. No app calculation logic or Excel workbook logic was updated.

## Method

- Source PDF graphs were vector drawings, not low-resolution raster scans.
- Curves were extracted from PDF drawing paths using PyMuPDF, including Bezier and line path commands.
- Plot axes were calibrated with piecewise linear transforms from labeled API/US tick marks.
- This package supersedes the earlier first-pass endpoint-span affine calibration.
- Points were generated at curve endpoints/control breakpoints, existing spreadsheet x-values inside the curve range, Annex B control x-values, and uniform in-range samples.
- OCR was not used for curve digitization.
- The normalized lookup workbook was generated with `openpyxl` because `@oai/artifact-tool` was unavailable in this session.

## Calibration

| Figure | Factor | Source page | Axis x range | Axis y range | Output x units | Output y units | Curves | Points |
|---|---:|---|---:|---:|---|---|---:|---:|
| Figure 3 | KHe | PDF page 19 / API page 13 | 0.0 to 0.08 | 0.0 to 12000.0 | tw/D | dimensionless | 4 | 216 |
| Figure 4 | Be | PDF page 19 / API page 13 | 0.0 to 32.0 | 0.0 to 1.5 | H/Bd | dimensionless | 2 | 127 |
| Figure 5 | Ee | PDF page 20 / API page 14 | 1.0 to 1.3 | 0.8 to 1.4 | Bd/D | dimensionless | 1 | 37 |
| Figure 7 | Fi | PDF page 22 / API page 16 | 1.0 to 2.0 | 0.0 to 30.0 | ft | dimensionless | 2 | 44 |
| Figure 8 | KHr | PDF page 23 / API page 17 | 0.0 to 0.08 | 0.0 to 500.0 | tw/D | dimensionless | 3 | 124 |
| Figure 9 | GHr | PDF page 24 / API page 18 | 0.0 to 42.0 | 0.0 to 1.25 | in | dimensionless | 3 | 122 |
| Figure 10 | NH | PDF page 25 / API page 19 | 0.0 to 42.0 | 0.5 to 2.0 | in | dimensionless | 3 | 98 |
| Figure 11 | KLr | PDF page 25 / API page 19 | 0.0 to 0.08 | 0.0 to 600.0 | tw/D | dimensionless | 3 | 110 |
| Figure 12 | GLr | PDF page 26 / API page 20 | 0.0 to 42.0 | 0.0 to 2.5 | in | dimensionless | 3 | 119 |
| Figure 13 | NL | PDF page 26 / API page 20 | 0.0 to 42.0 | 0.5 to 2.0 | in | dimensionless | 3 | 104 |
| Figure 14 | KHh | PDF page 27 / API page 21 | 0.0 to 0.08 | 0.0 to 25.0 | tw/D | dimensionless | 3 | 148 |
| Figure 15 | GHh | PDF page 28 / API page 22 | 0.0 to 42.0 | 0.0 to 2.0 | in | dimensionless | 4 | 183 |
| Figure 16 | KLh | PDF page 29 / API page 23 | 0.0 to 0.08 | 0.0 to 25.0 | tw/D | dimensionless | 3 | 121 |
| Figure 17 | GLh | PDF page 29 / API page 23 | 0.0 to 42.0 | 0.0 to 3.0 | in | dimensionless | 4 | 176 |
| Figure 18-A | RF | PDF page 34 / API page 28 | 0.0 to 42.0 | 0.0 to 1.0 | in | dimensionless | 3 | 54 |
| Figure 18-B | RF | PDF page 34 / API page 28 | 0.0 to 42.0 | 0.0 to 1.0 | in | dimensionless | 3 | 54 |

Calibration metadata with PDF frame coordinates, labeled tick controls, and drawing IDs is saved in `calibration_metadata.json`; point-level PDF coordinates are saved in `digitized_points_provenance.csv`.

## Calibration QA

| Figure | x-axis tick controls | y-axis tick controls | Max page residual | Ignored axes/ticks |
|---|---|---|---:|---|
| Figure 3 | 0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08 | 0.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0, 9000.0, 10000.0, 11000.0, 12000.0 | 0 | right-side duplicate or secondary ticks when present; top duplicate ticks |
| Figure 4 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0 | 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5 | 0 | right-side duplicate or secondary ticks when present; top duplicate ticks |
| Figure 5 | 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3 | 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4 | 0 | none |
| Figure 7 | 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0 | 1.0, 1.25, 1.5, 1.75, 2.0 | 0 | right metric depth axis |
| Figure 8 | 0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08 | 0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0 | 0 | right-side duplicate or secondary ticks when present; top duplicate ticks |
| Figure 9 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.0, 0.25, 0.5, 0.75, 1.0, 1.25 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 10 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 11 | 0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08 | 0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0 | 0 | right-side duplicate or secondary ticks when present; top duplicate ticks |
| Figure 12 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 13 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 14 | 0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08 | 0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0 | 0 | right-side duplicate or secondary ticks when present; top duplicate ticks |
| Figure 15 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.0, 0.5, 1.0, 1.5, 2.0 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 16 | 0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08 | 0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0 | 0 | right-side duplicate or secondary ticks when present; top duplicate ticks |
| Figure 17 | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 18-A | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |
| Figure 18-B | 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0 | 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 | 0 | right-side duplicate or secondary ticks when present; top metric diameter axis |

## Curves Captured

- Figure 3 KHe: E_prime_ksi=0.2 (54 pts), E_prime_ksi=0.5 (53 pts), E_prime_ksi=1.0 (56 pts), E_prime_ksi=2.0 (53 pts)
- Figure 4 Be: soil_type=A (64 pts), soil_type=B (63 pts)
- Figure 5 Ee: Ee (37 pts)
- Figure 7 Fi: crossing=highway (23 pts), crossing=railroad (21 pts)
- Figure 8 KHr: Er_ksi=5 (41 pts), Er_ksi=10 (42 pts), Er_ksi=20 (41 pts)
- Figure 9 GHr: H_ft=6 (41 pts), H_ft=10 (40 pts), H_ft=14 (41 pts)
- Figure 10 NH: H_ft=6 (34 pts), H_ft=10 (32 pts), H_ft=14 (32 pts)
- Figure 11 KLr: Er_ksi=5 (37 pts), Er_ksi=10 (37 pts), Er_ksi=20 (36 pts)
- Figure 12 GLr: H_ft=6 (40 pts), H_ft=10 (40 pts), H_ft=14 (39 pts)
- Figure 13 NL: H_ft=6 (35 pts), H_ft=10 (34 pts), H_ft=14 (35 pts)
- Figure 14 KHh: Er_ksi=5 (49 pts), Er_ksi=10 (50 pts), Er_ksi=20 (49 pts)
- Figure 15 GHh: H_ft=3_to_4 (45 pts), H_ft=6 (45 pts), H_ft=8 (44 pts), H_ft=10 (49 pts)
- Figure 16 KLh: Er_ksi=5 (40 pts), Er_ksi=10 (41 pts), Er_ksi=20 (40 pts)
- Figure 17 GLh: H_ft=3_to_4 (44 pts), H_ft=6 (45 pts), H_ft=8 (43 pts), H_ft=10 (44 pts)
- Figure 18-A RF: H_ft=6 (18 pts), H_ft=10 (18 pts), H_ft=14 (18 pts)
- Figure 18-B RF: H_ft=6 (18 pts), H_ft=10 (18 pts), H_ft=14 (18 pts)

## Assumptions And Limitations

- The PDF vector paths are treated as the controlling representation of the published graphs.
- The prior endpoint-span calibration has been superseded; use only the piecewise labeled-tick outputs in this folder.
- Leader arrows, tick marks, labels, and diagram callouts were excluded by drawing ID and stroke geometry.
- Figure 3 has a single visible common tail after KHe curves converge; that tail is reused for the higher E' curves after their unique strokes end and is identified in notes.
- Spreadsheet rows outside the drawn/API graph range are not extrapolated; they are labeled as guardrail/non-API-derived review rows.
- Figure 7 is plotted with Fi on the horizontal axis and depth on the vertical axis; the output tables normalize x to depth H for interpolation.
- Digitized values are graph-derived and may differ from Annex B rounded example values because Annex B values are rounded to engineering precision.

## Annex B Control Points

Status counts: {'FAIL': 1, 'PASS': 8, 'REVIEW': 5}

| Factor | Figure | API Annex B | Digitized | Spreadsheet | App table | Status |
|---|---|---:|---:|---:|---:|---|
| KHe | Figure 3 | 3024.0 | 2632.836699 | 2632.836699 | 2663.0 | FAIL |
| Be | Figure 4 | 1.09 | 1.071669 | 1.070535 | 1.0676 | PASS |
| Ee | Figure 5 | 1.11 | 1.106553 | 1.107279 | 1.11042 | PASS |
| Fi | Figure 7 | 1.47 | 1.480368 | 1.478814 | 1.47622 | REVIEW |
| KHr | Figure 8 | 332.0 | 325.604485 | 323.200702 | 324.532625 | REVIEW |
| GHr | Figure 9 | 0.98 | 0.984063 | 0.986019 | 0.98525 | PASS |
| NH | Figure 10 | 1.11 | 1.11601 | 1.141187 | 1.139877 | PASS |
| KLr | Figure 11 | 317.0 | 314.10277 | 314.10277 | 313.0 | PASS |
| GLr | Figure 12 | 0.98 | 0.976824 | 0.977771 | 0.971625 | PASS |
| NL | Figure 13 | 1.0 | 1.020467 | 1.020591 | 1.020729 | REVIEW |
| KHh | Figure 14 | 14.3 | 14.089377 | 14.074136 | 14.134633 | PASS |
| GHh | Figure 15 | 0.99 | 1.014641 | 1.015213 | 1.01675 | REVIEW |
| KLh | Figure 16 | 9.9 | 9.749911 | 9.749911 | 9.767 | REVIEW |
| GLh | Figure 17 | 1.01 | 0.999894 | 1.004673 | 1.0025 | PASS |

## Spreadsheet Comparison

Status counts: {'REVIEW': 153, 'PASS': 559}
Superseded first-pass endpoint-span status counts: {'PASS': 413, 'REVIEW': 156, 'FAIL': 143}
KHe failures did not remain after tick-calibrated correction.

| Factor | PASS | REVIEW | FAIL |
|---|---:|---:|---:|
| Be | 120 | 16 | 0 |
| Ee | 10 | 6 | 0 |
| Fi | 4 | 4 | 0 |
| GHh | 51 | 13 | 0 |
| GHr | 28 | 8 | 0 |
| GLh | 48 | 12 | 0 |
| GLr | 20 | 10 | 0 |
| KHe | 148 | 28 | 0 |
| KHh | 52 | 8 | 0 |
| KHr | 27 | 9 | 0 |
| KLh | 26 | 10 | 0 |
| KLr | 17 | 7 | 0 |
| NH | 1 | 11 | 0 |
| NL | 7 | 11 | 0 |

### Factors That Pass

None as a complete factor family.

### Factors Needing Review

Be, Ee, Fi, GHh, GHr, GLh, GLr, KHe, KHh, KHr, KLh, KLr, NH, NL

### Factors That Fail

None.

## Recommended Spreadsheet Corrections

- No material value replacements were identified by the configured tolerances.
- Remove, clamp, or explicitly label rows outside the API graph range as spreadsheet guardrails rather than API-derived values.
- Update app standards tables only after the workbook corrections are reviewed and approved, because the current app tables mirror the workbook tables.
- Preserve `calibration_metadata.json`, provenance CSV, and overlay PNGs with any future table revision so reviewers can reproduce the source values.

## Source Of Truth Conclusion

The current spreadsheets should not yet be treated as API-verified source of truth. They contain table values and guardrail rows that require engineering review against the digitized API graph package.

## Files Created

- `figure_03_KHe.csv`
- `figure_04_Be.csv`
- `figure_05_Ee.csv`
- `figure_07_Fi.csv`
- `figure_08_KHr.csv`
- `figure_09_GHr.csv`
- `figure_10_NH.csv`
- `figure_11_KLr.csv`
- `figure_12_GLr.csv`
- `figure_13_NL.csv`
- `figure_14_KHh.csv`
- `figure_15_GHh.csv`
- `figure_16_KLh.csv`
- `figure_17_GLh.csv`
- `figure_18A_RF.csv`
- `figure_18B_RF.csv`
- `api1102_digitized_lookup_tables.xlsx`
- `spreadsheet_table_comparison.csv`
- `annex_b_control_point_check.csv`
- `calibration_metadata.json`
- `digitized_points_provenance.csv`
- `viewer_manifest.json`
- `graph_underlays/*.png`
- `overlays/*.png`
- `source_page_images/*.png`
