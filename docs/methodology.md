# Methodology & Decisions Log

This file records real decisions made during the build, as they're made — not written
retroactively. It's what turns a working pipeline into a defensible piece of work: proof
of judgment, not just a list of finished features.

## Core hypothesis (stated before seeing Stage 4 results)
Does LLM-extracted urgency scoring (from ReliefWeb/GDELT report text) improve district-week
severity prediction over hazard data alone (river discharge, rainfall)? A negative result
here is a legitimate, reportable finding — not a failure.

## Validation strategy: why one event alone isn't sufficient proof

An important distinction, worth being explicit about before more data is collected:

**Within-event validation (Pakistan 2022 alone):** even a single flood event has real
variation to split on — 138 districts across multiple provinces, and multiple weeks as
the flood evolved (roughly June-October 2022). Spatial block CV (train on some provinces'
districts, test on others) and temporal block CV (train on early weeks, test on later
weeks) — both already specified in the project plan — can be applied within this one
event. This is a legitimate, necessary test, but it is a **weaker** one: it only shows
the model works within the specific conditions of this one flood (one river system, one
set of reporting agencies, one season). A model could pass this test purely by learning
quirks specific to Pakistan 2022, without having learned anything that generalizes.

**Cross-event validation (the actual proof of generalization):** the rigorous test this
project is ultimately built for is training on one or more events and testing on a
**completely separate, held-out flood event the model has never seen** — ideally in a
different country, with a different river system and different reporting agencies. This
is why the project plan always specified multiple validation events (5-8, across
Pakistan, Bangladesh, Philippines, etc.), not just one.

**Decision:** Pakistan (2022 floods) is being built first and completely, end-to-end,
because you cannot test generalization to a second country before the first one works at
all. This is explicitly **phase one — "get the pipeline working correctly," not
"prove the pipeline generalizes."** The genuine test of generalization comes once at
least one additional, independent country/event (Bangladesh is the current leading
candidate, given existing GloFAS tutorial precedent for a 2022 Bangladesh flood) is added
and used as a true held-out test, never touched during development of the Pakistan
pipeline. Until that second event exists, all results should be reported and interpreted
as "the pipeline works on Pakistan 2022," not as a general claim about flood prediction.

## River discharge & rainfall data (river/rainfall data collection)

**What is being extracted:** for each of the 138 real districts, for each week in the
chosen time window, two structured numeric values:
- **River discharge** — how much water is flowing through the nearest major river to
  that district that week (from GloFAS, via the Open-Meteo Flood API)
- **Rainfall** — total rainfall for that district/week (from CHIRPS, via Google Earth
  Engine)

**Sources chosen:**
- **River discharge: Open-Meteo Flood API** (free, no registration) — a wrapper around
  GloFAS data. Coordinates for each district are computed from the district's real GADM
  `geometry` (a representative point, e.g. centroid).
- **Rainfall: CHIRPS via Google Earth Engine** (free, requires one-time Earth Engine
  registration — the same registration needed later for Prithvi/satellite imagery in
  Stage 5, so no new platform to learn).

Both were adopted as reasonable starting points based on general accessibility, not yet
verified with the same rigor as GADM (no real values pulled and inspected yet). This
verification is the immediate next step before building the full ingestion function —
matching the same "open the file and look before trusting it" approach used for GADM.

## Time window for hazard data collection

**Why not flood-period-only:** if only flood-period data is collected, every row would
represent a flooded district-week, giving the model no "calm" examples to contrast
against — directly conflicting with the class-imbalance handling already specified in
the project plan (downsampling assumes both flood and non-flood examples exist to sample
from). A hazard reading (e.g. rainfall) is also only meaningful relative to a district's
normal baseline, which requires seeing calm-period data for that same district.

**Why not extending significantly past the flood's end:** humanitarian reporting
(WASH interventions, displacement, rebuilding) typically continues well after hazard
conditions (river discharge, rainfall) return to normal. Including an extended
post-flood window risks weeks where hazard data looks calm but report text still reads
as urgent — a contaminated, ambiguous signal that is neither a clean "flood" nor a clean
"calm" example. This directly conflicts with wanting a clean contrast between the two
classes. Pre-flood data does not have this problem, since it is unambiguously calm on
both hazard data and report text.

**Decision: pre-flood baseline + flood period only, no extended post-flood window.**

**Real dates used, with sourcing:**
- Flood onset: **14 June 2022** — consistently cited across sources (NDMA's own count,
  Wikipedia, Britannica, multiple ReliefWeb/OCHA situation reports all anchor to
  mid-June 2022 as when monsoon flooding began).
- Flood period end: genuinely variable across sources — Wikipedia/Britannica say
  "June to October 2022"; Center for Disaster Philanthropy extends to 18 November 2022;
  one ReliefWeb report notes Dadu and Jamshoro specifically were expected to remain
  partially inundated until the end of the year. **31 October 2022** was chosen as the
  cutoff — within every source's cited range, while avoiding the extended recovery-period
  window that risks report-text contamination described above.
- **Final window: 1 June 2021 to 31 October 2022** (window start rounded to the 1st of
  the month for cleaner date-range queries; two additional weeks of unambiguous
  pre-flood baseline data, no material downside).

**Known limitation, stated honestly:** since some districts (Dadu, Jamshoro specifically)
remained inundated past the October 31 cutoff, a single fixed end date is not equally
"clean" for every district — a small number of districts may still show elevated hazard
readings right at the window's end. This is noted as a real, minor limitation rather than
treated as a fully solved edge case.

## River discharge data: full coordinate-matching investigation

This section documents the complete investigation into river-discharge query-point
selection, from the initial centroid failure through to the decision to switch data
sources. Written as a narrative log rather than a single conclusion, since the process
of ruling out approaches is itself part of the project's methodology.

### Phase 1: centroid failure (Dadu, Sukkur)
District centroids (from GADM `geometry`) were tested as query coordinates against the
Open-Meteo Flood API (a free GloFAS wrapper). Dadu's centroid returned discharge peaking
at ~39 m³/s; Sukkur's centroid (despite Sukkur being the site of the Sukkur Barrage, a
major Indus structure) returned only ~11.4 m³/s. A manually-placed coordinate directly
on the Indus at Sukkur Barrage (27.6994°N, 68.8492°E) returned values in the thousands
(peaking ~13,600 m³/s), confirming the *source* was reliable but the *centroid* was not
a usable query coordinate — GloFAS/Open-Meteo's 5km-resolution nearest-river matching
frequently locks onto a minor tributary near an administrative centroid rather than the
major river relevant to the district.

### Phase 2: HydroRIVERS-based reach selection and point placement
**Source adopted:** HydroRIVERS (HydroSHEDS/WWF), a free global river-network line
dataset, intersected against each district's real GADM polygon (not a bounding box —
an early bbox-based test overcounted reaches by ~3x, 91,462 vs. the true 31,769 within
Pakistan's actual boundary).

**Selection attribute:** `DIS_AV_CMS` (modeled long-term average discharge) was chosen
over `UPLAND_SKM` (drainage area) as the primary criterion for picking "the major river"
among candidates intersecting a district, specifically because large arid catchments
(common in Balochistan) can have large drainage area but negligible real flow —
`UPLAND_SKM` would misrank these as major. Important caveat, resolved through discussion:
`DIS_AV_CMS` carries a documented ~35% average error (per HydroRIVERS' own technical
documentation), worse in arid/glacier-fed regions — but this error is used here only for
*relative ranking* among candidates (which reach is biggest), not as an *absolute value*
ingested into the model, and a systematic ~35% error is unlikely to flip an obviously
major river against an obviously minor one. `UPLAND_SKM` was retained as a secondary
cross-check rather than discarded. A second, Pakistan-specific caveat: `DIS_AV_CMS` is a
*naturalized* flow estimate that does not model human water management — the Indus basin
is one of the most heavily engineered river systems in the world (Indus Basin Irrigation
System, extensive canal off-takes), which may explain why discharge appears to decline
between the Punjab confluence and Sukkur in this dataset, though this is a plausible
hypothesis, not confirmed — ordinary natural transmission losses in an arid basin are an
equally consistent alternative explanation.

**Point placement on the selected reach:** tested midpoint (`.interpolate(0.5)`), then
both endpoints, then multi-point grid search along and around the reach. Results were
inconsistent and reach-specific:
- Sukkur: the reach's downstream endpoint (a junction node) gave a correct result;
  interior points did not.
- Dadu: no point along the selected reach or one reach further downstream gave a
  correct result.
- A full 138-district run (using highest-`DIS_AV_CMS` candidate reach at `ORD_FLOW`≤6,
  both endpoints tested) found: 11 districts with no candidate reach at this threshold;
  of the 127 tested, 79 (62%) had a plausible peak-to-average ratio (>0.5), 48 (38%)
  showed the same near-zero failure pattern as Dadu.
- **This 62% figure should not be read as a validated accuracy rate.** Only one district
  (Sukkur) was independently verified against real-world ground truth at the time of
  this run. A geographic/provincial cross-reference of the results suggested three
  distinct sub-patterns rather than random noise: (a) some low ratios are legitimately
  correct (minor hill-torrent districts in KP, glacier-fed upper Gilgit-Baltistan/AJK
  districts, and districts where both HydroRIVERS and Open-Meteo agree on near-zero
  flow); (b) a cluster of eastern Punjab low-ratio districts is plausibly explained by
  the Indus Waters Treaty (which allocates the Ravi/Beas/Sutlej "Eastern rivers"
  primarily to India — a naturalized discharge model would not know to account for this
  diversion) — flagged as a plausible, not confirmed, hypothesis; (c) a genuine,
  unexplained failure cluster along the Indus mainstem itself (Dadu, Thatta,
  DeraIsmailKhan, Mianwali, Ghotki, NaushahroFiroz, NawabShah, RahimyarKhan) where the
  query point was confirmed geometrically inside the correct district, on a correctly
  major reach, and still returned near-zero.

**Grid-search follow-up on 5 ground-truthed districts** (Thatta, Multan, Quetta,
Charsadda, JhalMagsi — each independently researched for real geography before testing):
found a working point for Thatta and confirmed Quetta's "no candidate" result was a
threshold artifact (a real, smaller river exists but falls below the `ORD_FLOW`≤6 cutoff),
correctly re-interpreted JhalMagsi's extreme outlier ratio as a real signal mislabeled by
poor reach-selection rather than noise, and left Multan fully unresolved (no point within
5km along or around the selected reach showed any signal above ~1.7 m³/s). **A
methodological gap was identified in this specific test**: unlike the Quetta grid (which
was explicitly polygon-constrained), the river-following grid searches for Thatta and
JhalMagsi were not checked against the district's own polygon boundary — Thatta's
"winning" point returned a peak value identical to already-known-good values from the
neighboring Hyderabad/Matiari district, raising the possibility the result reflects
geographic bleed into a neighboring district rather than a genuine fix for Thatta itself.
This was not resolved before the approach was superseded (see Phase 3).

### Phase 3: decision to switch to native GloFAS data (current approach)
**Root cause identified:** HydroRIVERS and Open-Meteo/GloFAS are two independently-built
hydrography models (different source resolution, different organizations) that do not
reliably agree on exact river location below ~5km precision. No amount of point-selection
logic applied to HydroRIVERS' geometry can fully fix a disagreement between two separate
models of where a river actually is.

**How real operational systems avoid this problem:** researched Google Flood Hub as a
reference point. It anchors to real, physical river gauge locations ("target gauges")
rather than computing coordinates from administrative boundaries, and uses trained
LSTM models (published in Nature) to infer conditions at ungauged locations from
patterns learned at gauged ones — a fundamentally different, training-based strategy
requiring institutional data access and research infrastructure beyond this project's
scope. This did not provide a directly usable technique, but confirmed the underlying
problem (coordinate-to-river matching for hydrological data) is a genuine, actively
researched difficulty in this field, not a gap in project execution.

**Decision:** switch from the third-party HydroRIVERS dataset to GloFAS's own natively
published ancillary data (upstream area grid, and/or GloFAS's own defined "reporting
points" for major river sections with upstream area >1,000 km²), accessed via the
official Copernicus Early Warning Data Store (EWDS), rather than the Open-Meteo wrapper.
Rationale: this uses GloFAS's own internal definition of river geometry for both
locating and querying discharge, eliminating the cross-model disagreement at its root
rather than continuing to work around it with a third-party dataset. Cost: requires EWDS
registration and the `cdsapi` package/NetCDF handling, a meaningfully larger technical
lift than the Open-Meteo wrapper — accepted as justified given it targets the actual
root cause rather than another symptom.

**Status: in progress.** EWDS account registration underway. Next validation step planned:
re-test Sukkur (known-good) and Multan (confirmed unresolved failure) against
GloFAS-native coordinates before scaling to all 138 districts.

## Country and event selection

**Country chosen: Pakistan.** Selected after comparing Pakistan, Bangladesh, Philippines,
India, and Indonesia against project needs: report density (ReliefWeb/GDELT coverage),
administrative clarity (GADM structure), structured data coverage (GloFAS river basin
modeling), language friction, and availability of a single well-defined flood event.
Pakistan ranked highest primarily due to the scale of international humanitarian response
to the 2022 floods (~$30B+ damage, 1,700+ deaths), which translates directly into report
density for our two text sources. India was considered but tends to have thinner ReliefWeb
coverage, since disaster response there is generally managed domestically rather than
through the international humanitarian channels ReliefWeb aggregates.

**Event chosen: 2022 Pakistan floods** (to be narrowed to specific weeks/districts once
Stage 1 ingestion for hazard and text data begins).

## Data sources: decisions and exclusions

- **Reddit:** considered, cut. Free-tier API restrictions and loss of reliable historical
  search (post-2023 pricing changes, Pushshift access loss) make historical backtesting
  impractical.
- **Social media scraping (Twitter/X, Instagram, Facebook):** excluded on ToS, cost, and
  privacy grounds.
- **National disaster authority bulletins (NDMA, etc.), individual NGO sitreps, Telegram,
  Ushahidi deployments:** considered, not used as primary sources. Mostly redundant with
  what ReliefWeb/GDELT already aggregate at scale, with added friction (PDF-only formats,
  local-language content, inconsistent availability across events) not justified given
  time budget.
- **Chosen unstructured sources: ReliefWeb + GDELT** — both free, no real registration
  friction, and both deeply historical by design (unlike Reddit).
- **Chosen structured sources: GloFAS (via Open-Meteo Flood API) for river discharge,
  CHIRPS (via Google Earth Engine) for rainfall, EM-DAT for historical impact records,
  GADM for district boundaries.**

## District boundary data (GADM) — findings and decisions

**Source:** GADM v4.1, Pakistan, GeoJSON, administrative level 3 (Districts).
File: `data/raw/gadm_pakistan/gadm41_PAK_3.json`

**Why level 3, not level 2:** Pakistan's administrative hierarchy is Province → Division →
District → Tehsil. Level 2 in GADM corresponds to Divisions (32 units, too coarse — e.g.
"Multan Division" rather than individual districts within it). Level 3 corresponds to
Districts (141 units), which is the granularity this project actually needs. This was
discovered by first loading level 2 and finding that known districts from early testing
(Dadu, Sanghar) were absent — Multan appeared only by coincidence, since it happens to be
both a Division name and a District name.

**Problems found in the level-3 file, and how each was handled:**

1. **Country-code miscoding.** 14 of 141 districts are coded `GID_0 = "Z06"` instead of
   `"PAK"` — 8 in Azad Kashmir, 6 in Gilgit-Baltistan. A naive filter of `GID_0 == "PAK"`
   would silently drop all 14, despite this being a Pakistan-downloaded file.
   **Decision:** do not filter by `GID_0` alone. Of these 14, 11 are genuinely
   Pakistan-administered (Azad Kashmir + Gilgit-Baltistan) and are retained.

2. **Three districts are not actually Pakistan-administered.** Kargil, Ladakh(Leh), and
   Kupwara(GilgitWazarat) are Indian-administered territory (part of Ladakh/Jammu &
   Kashmir), listed here nested under Pakistan's claimed Gilgit-Baltistan structure —
   reflecting a claimed rather than de facto boundary.
   **Decision:** exclude these 3 from the working district list. This is a practical
   decision, not a political one: the project models Pakistan's administrative flood
   response system (humanitarian reports, hazard data pipelines relevant to Pakistan),
   which does not govern these areas, so including them would produce meaningless results
   for those rows.

3. **District names are not a reliable unique identifier.** 4 base-name collision pairs
   exist in the file: `Gujranwala1`/`Gujranwala2`, `Narowal1`/`Narowal2` (both under
   Gujranwala division, Punjab), `Okara`/`Okara1` (Lahore division, Punjab), and
   `DisputedArea1`/`DisputedArea2` (Kalat division, Balochistan — a separate, unrelated
   territorial ambiguity from the Kashmir coding issue above). No exact duplicate names
   exist; all collisions are disambiguated by distinct `GID_3` values.
   **Decision:** use `GID_3` as the canonical `district_id` throughout the project.
   `NAME_3` is used for display only, never as a key.

**Verified clean (checked, not assumed):** no duplicate `GID_3` codes, no null or missing
geometries, no missing `NAME_3` values, all geometries are valid `MultiPolygon` shapes
within Pakistan's expected coordinate range, and `GID_2`-to-level-2-file linkage is fully
consistent in both directions.

**Still open:**
- Whether `GID_3` values are stable across GADM versions (relevant given GADM v5 may now
  be available; this project has deliberately pinned v4.1 for consistency).
- Whether every district needed for the final chosen 2022 flood validation weeks is
  correctly and completely represented here — only Dadu, Sanghar, and Multan have been
  spot-checked so far.

## Boundaries pinning
- Pinned GADM version: **v4.1**
- Rationale: consistency with existing GloFAS/Copernicus tutorials referenced in
  `docs/data-sources.md`, avoiding a silent version mismatch mid-project.

## Findings (to be filled in during Stage 4)
- Baseline (hazard-only) performance: _pending_
- Augmented (hazard + LLM) performance: _pending_
- SHAP finding on where/whether LLM features added signal: _pending_

## What I'd do differently next time
_(To be filled in at the end.)_
