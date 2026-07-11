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

## River discharge data: centroid coordinate problem (finding, not yet resolved)

**What was tested:** before building the real river-discharge ingestion function, two
real districts were tested individually against the Open-Meteo Flood API (GloFAS
wrapper), using each district's geometric centroid (computed from its real GADM
`geometry`) as the query coordinate — matching the same "verify on one real example
before scaling" discipline used for the GADM boundary data.

**Test 1 — Dadu** (centroid: 26.8277°N, 67.5510°E): returned discharge values peaking at
~39 around 19-20 August 2022. Timing matched Dadu's known flood peak, but the magnitude
is implausibly small for any Indus-connected waterway during this event.

**Test 2 — Sukkur** (centroid: 27.5144°N, 69.2009°E): returned discharge values peaking
at ~11.4 around 20 August 2022 — same suspicious pattern. This result matters more than
Dadu's, because Sukkur is the site of the Sukkur Barrage, a major structure sitting
directly on the Indus mainstem. A district whose entire geographic significance is the
Indus running through it should not return near-zero discharge.

**Diagnostic test — manually-placed coordinate:** querying the same date range at
27.6994°N, 68.8492°E (Sukkur Barrage's actual location on the Indus, not the district
centroid) returned values in the thousands (peaking ~13,600 m³/s in early July, staying
elevated through August, second peak ~13,400 on 28 August) — the correct order of
magnitude for the Indus during this event, and matching the real flood timeline.

**Finding:** district administrative centroids are not reliable query coordinates for
river discharge. GloFAS/Open-Meteo's 5km-resolution nearest-river matching, given a
centroid, frequently locks onto a small local tributary or drainage line rather than the
major river actually relevant to that district. This is a structural problem affecting
all 138 districts, not an isolated edge case — confirmed by testing two independent
districts and getting the same failure pattern, then confirming the fix (a correctly
-placed coordinate) resolves it.

**Status:** blocking issue for real river-discharge ingestion. Naive centroid-based
querying cannot be used. Fix not yet decided — options being considered: (1) manually
curated "river snap point" per district, (2) intersecting each district's geometry with
a known river-line dataset to find an actual on-river coordinate programmatically.
Decision and reasoning to be logged here once made.

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
