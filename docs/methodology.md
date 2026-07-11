# Methodology & Decisions Log

This file records real decisions made during the build, as they're made — not written
retroactively. It's what turns a working pipeline into a defensible piece of work: proof
of judgment, not just a list of finished features.

## Core hypothesis (stated before seeing Stage 4 results)
Does LLM-extracted urgency scoring (from ReliefWeb/GDELT report text) improve district-week
severity prediction over hazard data alone (river discharge, rainfall)? A negative result
here is a legitimate, reportable finding — not a failure.

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
