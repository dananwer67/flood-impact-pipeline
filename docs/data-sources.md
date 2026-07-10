# Data Sources — Verified Access Details

This document lists every real data source for the project, with actual verified access
methods, URLs, and honest notes on friction/cost. Compiled before starting Stage 1 so
ingestion code has concrete starting points rather than vague references.

---

## Structured hazard data

### GloFAS (river discharge)
Two realistic access paths, very different difficulty levels:

- **Easy path (recommended to start): Open-Meteo Flood API** — a free, no-registration
  wrapper around GloFAS data. Give it a coordinate, get river discharge back as JSON.
  Docs: https://open-meteo.com/en/docs/flood-api
  Good enough for prototyping and even for real ingestion — seamless data from 1984
  to present. Note: 5km resolution, so closest river might occasionally be misidentified;
  varying coordinates slightly can help.
- **Full/official path: Copernicus Early Warning Data Store (EWDS)** — requires free
  registration (ECMWF account) and the `cdsapi` Python package. More granular, official,
  used in real GloFAS tutorials (including one specifically analyzing the June 2022
  Bangladesh flood — good template to adapt).
  Datasets page: https://ewds.climate.copernicus.eu/datasets
  Tutorial adaptable to our use case: https://ecmwf-projects.github.io/copernicus-training-c3s/glofas-bangladesh-floods.html

**Recommendation:** start with Open-Meteo for the walking-skeleton-to-real-data transition
(fast, zero setup). Move to EWDS/cdsapi later if more historical granularity is needed.

### EM-DAT (historical disaster records)
- Register (free, non-commercial use) at https://public.emdat.be/register
- Download as .xlsx via the "Access Data" tab after login
- Also has a GraphQL API and Python cookbook: https://files.emdat.be/docs/emdat_api_python.pdf
- **Easier alternative for aggregated figures:** EM-DAT summary data is also mirrored on
  HDX (see below) and accessible via the HDX API without separate EM-DAT registration —
  worth checking if HDX's version has enough detail before doing the full EM-DAT signup.

### HDX (Humanitarian Data Exchange)
- No API key needed for reading data (only needed if writing/uploading datasets)
- Recommended tool: `hdx-python-api` (`pip install hdx-python-api`)
- Example read pattern:
  ```python
  from hdx.api.configuration import Configuration
  from hdx.data.dataset import Dataset
  Configuration.create(hdx_site="prod", user_agent="flood_impact_pipeline", hdx_read_only=True)
  dataset = Dataset.read_from_hdx("dataset-name-here")
  ```
- Docs: https://hdx-python-api.readthedocs.io/

---

## Unstructured text data

### ReliefWeb (situation reports)
- **Completely free, no real registration** — just an `appname` parameter identifying
  your app (any descriptive string works, e.g. `flood_impact_pipeline`), used for their
  usage statistics, not an auth key
- No fees, no rate-limit-by-key — max 1000 results per call
- Example query:
  `https://api.reliefweb.int/v2/reports?appname=flood_impact_pipeline&query[value]=flood+Pakistan`
- Full docs: https://apidoc.reliefweb.int/
- Endpoints reference: https://apidoc.reliefweb.int/endpoints

### GDELT (global news signal)
- **Classic GDELT (recommended, free, no key):** the GDELT DOC 2.0 API for article
  search by keyword/date/country — simple GET requests, no signup.
  Overview: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- Raw Event/GKG database also downloadable as CSV, free, no key, back to 1979 (events)
  / 2015 (GKG 2.0): https://www.gdeltproject.org/data.html
- For bulk historical querying, Google BigQuery has a free 1TB/month quota (needs a
  Google Cloud account, but no cost within quota): search "gdelt-bq" in BigQuery
- **Important distinction:** there's a newer, separate commercial product called
  "GDELT Cloud" (gdeltcloud.com) — a paid/signup layer with its own API, NOT the same
  as the original free GDELT Project data. Use classic GDELT (gdeltproject.org), not
  GDELT Cloud, for this project.

### CHIRPS (rainfall)
- Climate Hazards Center's rainfall dataset — 30+ year, quasi-global (50°S-50°N, covers
  all our target countries), 0.05° resolution, combining satellite imagery with ground
  station data
- **Recommended access: Google Earth Engine** (`UCSB-CHG/CHIRPS/DAILY` collection) — free
  for research/education/nonprofit use, requires registering for Earth Engine access
  (same registration we'll already need for Prithvi/satellite imagery in Stage 5, so this
  doesn't add a new platform to learn)
- Example (Python, via `earthengine-api` or `geemap`):
  ```python
  import ee
  dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').filter(
      ee.Filter.date('2022-08-01', '2022-08-31')
  )
  ```
- **Version note:** CHIRPS v3 is now the current version; v2 production ends December
  2026. Use v3 for new work — same pin-and-document approach as the GADM version note
  below, so the choice is deliberate and recorded, not silently mixed later.
- Public domain data, free to use, citation appreciated but not required

---

## Satellite imagery & flood segmentation

### Prithvi (IBM/NASA geospatial foundation model)
- Open-source, free — published weights on Hugging Face
- Fine-tuned flood-detection checkpoint: `Prithvi-100M-sen1floods11` (or newer
  `Prithvi-EO-2.0` variants)
- Self-host via free Colab GPU tier for inference — no cost unless using managed
  hosted inference (Hugging Face Inference Endpoints, IBM watsonx), which isn't needed
  for this project's batch/retrospective use case
- Input requirement to plan for: expects Harmonized Landsat Sentinel-2 (HLS) imagery,
  specific spectral bands — sourcing/preparing this correctly is real work, budgeted
  into Stage 5, Weeks 15-16

### District boundaries: GADM
- Free download by country: https://gadm.org/download_country.html
- Non-commercial/academic use permitted; redistribution or commercial use requires
  permission — fine for this project
- **Note found during this search:** GADM v5 was scheduled for release around January
  2026, which has already passed as of the current date — worth checking
  https://gadm.org/data.html to see if v5 is now live before downloading. If so,
  decide deliberately whether to pin v4.1 (as originally planned, for consistency with
  older tutorials/precedent) or move the pin to v5 — but pin whichever is chosen and do
  not silently mix versions.

### Event selection archive: Sentinel Asia
- Public archive of officially-triggered emergency observations, Asia-Pacific,
  since 2007: https://sentinel-asia.org/EO/EmergencyObservation.html
- Article pages (dates, countries, disaster types) are public and usable for building
  the validation event shortlist
- Raw imagery/data access may require registration as a data provider/user under their
  cooperative charter — confirm this separately once actually pulling imagery, not
  assumed to be fully open

---

## Summary table

| Source | Registration needed? | Cost | Best for |
|---|---|---|---|
| Open-Meteo Flood API | No | Free | Quick GloFAS river discharge access |
| Copernicus EWDS (GloFAS official) | Yes (free ECMWF account) | Free | Deeper historical GloFAS granularity |
| EM-DAT | Yes (free, non-commercial) | Free | Historical disaster impact records |
| HDX | No (read-only) | Free | Aggregated humanitarian datasets |
| CHIRPS (via Earth Engine) | Yes (free Earth Engine registration) | Free | Rainfall data |
| ReliefWeb | No (just an appname string) | Free | Situation reports / text |
| GDELT (classic) | No | Free | Global news signal |
| Prithvi (self-hosted) | No | Free (Colab GPU) | Flood extent segmentation |
| GADM | No | Free (non-commercial) | District boundaries |
| Sentinel Asia | No (for browsing archive) | Free | Selecting validation events |
