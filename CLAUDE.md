## Project
Flood impact assessment pipeline for South and Southeast Asia. Combines structured
hazard data (GloFAS river discharge, EM-DAT historical records) with LLM-extracted
signals from humanitarian reports (ReliefWeb, GDELT) to rank districts by urgency of need.
Validated retrospectively against real historical floods (e.g. Pakistan 2022).

Full plan, architecture, data sources, and rationale: docs/flood-impact-project-plan.md
Read that file before proposing any structural changes.

## How we are building this — read this carefully
This project is being rebuilt slowly and deliberately so the person building it (a
university student, not yet an experienced developer) understands every piece, not
just ends up with working code. Because of this:

- Build ONE file, ONE function, or ONE small piece at a time. Never generate multiple
  files or a full stage in a single response.
- Before writing code, briefly explain in plain language what the piece does and why,
  as if to someone new to programming.
- Stop after each piece and wait for confirmation before moving to the next one.
- Do not skip ahead to later stages or add functionality that wasn't asked for, even
  if it seems like a natural next step.
- Prefer simple, readable code over clever or highly optimized code at this stage.

## Current status
Week 0 (terminal, git, venv, pip basics) is complete. Starting the "walking skeleton"
now — a deliberately crude, fake end-to-end version of the pipeline (fake data ->
fake LLM extraction -> fake scoring -> basic dashboard), built slowly, piece by piece.
Real Stage 1 (actual data ingestion) comes after the skeleton runs end to end.

## Stack (introduced only as each piece is actually built, not all at once)
- Python 3.11+, pandas
- Streamlit (dashboard)
- Later: Postgres, Airflow/Dagster, Great Expectations, Instructor/Outlines,
  scikit-learn/XGBoost, FastAPI, Docker, Leaflet.js/Mapbox GL

## Conventions
- Type hints on functions once we're past the very first, simplest versions
- Format with `black` before committing (introduced once the skeleton exists)
- Config-driven where possible: no hardcoded event lists or hyperparameters in code
- Never commit anything under data/raw, data/staging, data/curated, or .env
- One GADM boundary version pinned for the whole project (see project plan) — never
  silently update boundary files

## Don't
- Don't scrape Twitter/X, Instagram, Facebook, or news sites directly (ToS/legal — see plan doc)
- Don't use the Reddit API for historical backtesting (unreliable for past dates — see plan doc)
- Don't do live satellite/GEE raster fetches per request — precompute and cache for the
  fixed set of validation events instead
- Don't use a random train/test split for the ML model — spatial/temporal leakage risk.
  Use spatial or temporal block cross-validation.
- Don't treat LoRA fine-tuning as core scope — strict optional stretch goal, cut first
