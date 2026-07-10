# Flood Impact Assessment Pipeline — Full Project Plan

## 1. Project overview

**One-line pitch:** An end-to-end system that combines structured flood hazard data with LLM-extracted signals from humanitarian reports and news to identify which districts in South and Southeast Asia need help most urgently — validated against real historical floods, and presented as an interactive dashboard where a user can select a historical week, see the satellite flood-extent overlay, read the extracted report snippets driving the urgency score, and watch the prioritized district list update.

**Why this domain:**
- South and Southeast Asia is the most flood-exposed region in the world (Bangladesh, India, Pakistan, Philippines, Indonesia all rank among the highest globally for flood risk and population exposure).
- Real, open data exists for both the structured and unstructured halves of the pipeline.
- The domain has genuine commercial/humanitarian precedent (Floodbase, formerly Cloud to Street, has raised $24.1M+ and serves the World Food Programme, insurers, and governments) — proof this is a legitimate, not speculative, space.
- It touches every stage of the data lifecycle: data engineering, analysis, NLP/LLM, ML, and deployment — matching Data Analyst, Data Scientist, ML, Data Engineer, and AI/GenAI Engineer internship role types all at once.

**Time budget:** ~20 weeks (approx. 5 months), plus a preliminary Week 0 for foundational skills (see Section 3)
**Cost:** $0–$100 total (nearly everything used has a free tier sufficient for this scale)

**How this gets built:** one file, one function, one concept at a time — not large batched deliveries. Each piece is explained and understood before moving to the next, so the final result is something the builder can genuinely explain and defend, not just something that runs. This is slower than having an AI tool generate the whole pipeline at once, and that's intentional: the goal is real understanding, not just a working artifact.

---

## 2. Data sources

| Type | Source | What it provides |
|---|---|---|
| Structured (hazard) | GloFAS (Copernicus Global Flood Awareness System) | River discharge, flood forecasting data, global coverage |
| Structured (historical) | EM-DAT | International disaster database — dates, affected population, damage figures |
| Structured (humanitarian) | HDX (Humanitarian Data Exchange) | Flood/displacement datasets by country/region |
| Structured (geographic) | District boundary GeoJSON/shapefiles (e.g., GADM) | District-level polygons for mapping and ID resolution |
| Unstructured (reports) | ReliefWeb | Real humanitarian situation reports and news, global coverage |
| Unstructured (news, structured signal) | GDELT Project | Global news monitoring, extracts structured event data (location, tone, actors) at scale — free, no scraping needed |
| Satellite imagery | Sentinel Hub or Google Earth Engine (free tiers) | Satellite-derived flood extent for map overlay |
| Flood segmentation model | Prithvi (IBM/NASA geospatial foundation model, open-source via Hugging Face) | Pretrained, fine-tuned flood-detection model — produces validated flood extent masks from satellite imagery, rather than DIY thresholding |
| Event selection / archive | Sentinel Asia | Continuously maintained archive of officially-triggered emergency Earth-observation events across Asia-Pacific since 2007 — used to select validation events by confirmed date/country/disaster type rather than general knowledge |

**On Prithvi:** this is an open-source model, not a traditional paid API — free to self-host (e.g., via a Colab free-tier GPU) using published weights on Hugging Face. Paid hosted inference (Hugging Face Inference Endpoints, IBM watsonx) is only needed for managed, low-latency serving, which isn't required for this project's retrospective, batch-oriented use case.

**On Sentinel Asia:** article pages are public and usable for building the validation event list (confirmed dates, countries, disaster types). Access to the underlying raw satellite imagery/data may require registration as a data provider/user under their cooperative charter — check this separately when actually pulling imagery, rather than assuming full open access.

**Reddit was considered and cut.** Following Reddit's 2023+ API pricing overhaul, the free tier is heavily rate-limited and — more importantly — reliable historical search (paging back years to a specific week during, say, the 2022 Pakistan floods) is no longer practically available; the third-party archive (Pushshift) researchers used for this also lost full access around the same time. Since this project's entire validity rests on backtesting against specific historical weeks, fighting an API that isn't built for historical retrieval is a pure time sink with no payoff. GDELT and ReliefWeb are both deeply historical by design and cover the same ground without this problem. If an informal/social text layer is still desired later, an existing open-source Kaggle disaster-text dataset is a safer source than fighting a live API for old dates.

**Explicitly excluded:** Scraping BBC/CNN/etc. directly (ToS/copyright risk), scraping Twitter/X, Instagram, or Facebook (paid/restricted APIs, ToS violations, privacy concerns around individual disaster posts), and the Reddit API (unreliable historical retrieval, see note above). GDELT + ReliefWeb cover the unstructured text layer without these problems.

**Scope of historical coverage:**
- Structured data: as far back as cleanly available (post-2000 floor), since more data strengthens the ML model with no real downside.
- Text/validation events: 5–8 major, well-documented floods (roughly last 10–15 years, selected by actual report density, not just date) across Pakistan, Bangladesh, India, Philippines, and/or Indonesia — Sentinel Asia's archive of officially-triggered emergency observations is the recommended source for building this shortlist, since every entry has a confirmed date, country, and disaster type.

---

## 3. Week 0 — Foundations

Before Stage 1 begins, a short preliminary week (or two, if needed — no rush) covers the practical skills the project depends on that aren't yet second nature. This isn't about re-learning things already covered in coursework (Python fundamentals, pandas, basic sklearn, OOP, and algorithms are already solid from prior units) — it's specifically the hands-on, practical layer that coursework touched on only in theory or not at all:

- **Practical terminal/command-line use** — navigating folders, running commands, reading output
- **Git and GitHub, hands-on** — init, add, commit, push, pull, basic branching
- **Virtual environments and pip, hands-on** — creating, activating, installing into a venv
- **Practical SQL** — writing real queries against a real database, not just the conceptual overview from coursework
- **Working with APIs** — using the `requests` library, handling JSON responses

Everything else that's new (orchestration, Great Expectations, Instructor/Outlines, spatial/temporal cross-validation, FastAPI, Docker, geospatial tools) is introduced at the point in the plan where it's actually used, in context, rather than front-loaded here.

---

## 4. Architecture — five stages

### Stage 1: Data Engineering (Weeks 1–5)
**Goal:** ingestion pipeline structured for weekly, district-level granularity.

- Week 1: Repo setup, Postgres, environment config. Pull EM-DAT historical records.
- Week 2: Ingest GloFAS river discharge data + district boundary GeoJSON for target countries. **Pin one specific boundary dataset version (e.g., GADM v4.1) for the entire project.** Administrative boundaries in this region are fluid (districts split, renamed, or newly created — e.g., new upazilas in Bangladesh, new states/districts in India). Never update boundary files mid-project; instead, manually map any place name from a newer/older administrative structure back to your pinned version's polygons.
- Week 3: Build ReliefWeb + GDELT ingestion, tagged by date/week and location. **Critical sub-task: spatial entity resolution** — text sources reference places informally ("suburbs of Dhaka," "southern Sindh along the Indus"), not clean district IDs. Solve with GeoPy geocoding + a manual dictionary mapping major cities/rivers/regions to `district_id` for your chosen validation events. This must be solved here or Stage 3 stalls. **Also implement deduplication here:** GDELT is a firehose, and major floods get syndicated across hundreds of near-identical outlet articles. Ingesting hundreds of duplicate articles per district-week would artificially inflate urgency scores and waste LLM tokens downstream. Dedupe by unique title/URL, or use GDELT's own `NumArticles`/`NumMentions` and `GoldsteinScale` fields to collapse syndicated coverage into one event-signal per district-week before it reaches staging.
- Week 4: Buffer/catch-up week — deepen ReliefWeb/GDELT coverage, backfill any gaps in structured data, start drafting the location-mapping dictionary fully. (Originally a Reddit ingestion week; reassigned since Reddit was cut — see Section 2.)
- Week 5: Finalize schema — every record (structured or text) tagged by `event_id`, `district_id`, `week_number`. Wire up data validation (Great Expectations) and orchestration (Airflow or Dagster) so schema drift or broken sources alert immediately instead of silently poisoning downstream data.

**Learn:** SQL/Postgres, API integration, Airflow or Dagster, Great Expectations, GeoJSON/shapefiles, GeoPy geocoding.
**Free resources:** Airflow quickstart docs, Dagster tutorial, Great Expectations "Getting Started," freeCodeCamp SQL course.

### Stage 2: Data Analysis (Weeks 5–7)
- Exploratory analysis: rainfall/river-level vs. reported impact correlation, by district-week.
- Written narrative of patterns found per validation event.
- Early non-final Streamlit prototype to sanity-check data as you build.

**Learn:** pandas/seaborn/plotly, basic statistical testing, Streamlit basics.
**Free resources:** Kaggle pandas/visualization micro-courses, Streamlit docs tutorial.

### Stage 3: LLM/NLP Feature Extraction (Weeks 7–11)
- Weeks 7–8: Prompt design to extract need-type, urgency, and location from ReliefWeb/GDELT text, tagged to `district_id` + `week_number`. Use **Instructor or Outlines** to enforce schema-valid structured output directly, rather than hoping the model returns clean JSON. **Use batch processing (OpenAI Batch API or Anthropic Message Batches)** rather than real-time calls — since this pipeline runs entirely on historical data at weekly granularity, there's no need for live streaming responses, and batch processing gives a real cost discount (typically around 50%) in exchange for a turnaround measured in hours rather than seconds. Design the Stage 3 pipeline around batch jobs from the start rather than retrofitting it later. **Explicitly define humanitarian jargon in the system prompt** — ReliefWeb/HDX reports use NGO shorthand, not plain English (e.g., "Urgent WASH and NFI interventions required" instead of "people need clean water and blankets"). Key acronyms to define: WASH (Water, Sanitation, and Hygiene), NFI (Non-Food Items — blankets, tents), IDP (Internally Displaced Persons). Without this, the LLM will silently misjudge highly urgent reports as low-urgency, and the output will still look schema-valid, so this failure mode won't be obvious unless checked for directly.
- Week 9: Build your own hand-labeled ground-truth evaluation set. **This is the most important week of this stage — do not skip it.** Without it, you can't objectively prove later prompt iterations are actually improvements. Give whoever labels ground truth (even if it's just you) the same jargon glossary used in the system prompt, so labeling errors don't come from the same vocabulary gap you're trying to fix in the model.
- Week 10: Iterate on prompting strategies, measured against your evaluation set (precision/recall/F1).
- Week 11 (**strict stretch goal, first to cut if behind schedule**): Small LoRA/QLoRA fine-tuning experiment on a small open model (Llama 3.2 1B/3B, Qwen 1.5B), compared against prompting. Fine-tuning setup (environment, GPU memory, training stability) can eat days if not scoped tightly — do not let this threaten the core pipeline.

**Learn:** Prompt engineering, Instructor/Outlines, precision/recall/F1 evaluation methodology, Hugging Face basics, LoRA/PEFT (if pursuing stretch goal).
**Free resources:** Hugging Face NLP course, Hugging Face PEFT tutorial, Instructor/Outlines documentation.

### Stage 4: Machine Learning (Weeks 11–15) — the project's core thesis
**The central question:** does LLM-extracted urgency scoring improve prediction over hazard data alone? State this hypothesis explicitly in `methodology.md` *before* seeing results.

- Baseline model (structured-only: river discharge, rainfall, historical records) vs. LLM-augmented model (+ extracted urgency/need features), by district-week.
- **No random train/test split.** Neighboring districts flood together, so a random split lets the model "see" a district's neighbor from the same week during training and its match during testing — this produces misleadingly high accuracy from memorizing a week's weather pattern, not genuine generalization. Use **spatial block cross-validation** (train on Bangladesh/India, test on Pakistan) and, if time allows, **temporal block cross-validation** (train on 2010–2019 events, test on 2022 Pakistan floods) as a second, independent generalization check.
- **Handle class imbalance correctly and in the right order.** Most district-weeks will show zero flood impact ("peacetime" data), so an untreated dataset will be dominated by "no help needed" rows and the model will just learn to always predict that. Downsample peacetime weeks (e.g., one random non-flood week per region per active flood event, discarding the rest) — but do this *within* each train/test block from the step above, not before splitting, or you'll leak information across the block boundary while trying to fix the imbalance.
- Proper cross-validation, hyperparameter tuning.
- Error analysis — where and why the model misclassifies specific districts.
- SHAP interpretability on the best model — e.g., quantifying how much the LLM-extracted "urgency score" contributes to predicting severe impact, in a way you can state precisely to an interviewer. **Design this analysis to directly address the core thesis:** does unstructured text data catch signal that physical hazard data (river discharge) misses? If the data supports it, the strongest possible answer has a shape like "in most cases hazard data predicted baseline risk, but in [specific event], the LLM-extracted [specific feature] was the deciding factor that correctly flagged [specific districts] before [specific structured signal] caught up" — a concrete, falsifiable claim beats a vague one. This is a template for the shape of a strong finding, not a guaranteed result; report whatever SHAP actually shows, per the negative-result framing above.
- **Output an uncertainty/confidence signal alongside every urgency score, not just the score itself.** A bare point-estimate ("Urgency: 92") implicitly claims more certainty than any model actually has. Cheapest options: model confidence (e.g., prediction probability from the classifier) displayed next to the score, and/or an agreement score between the hazard-only baseline and the hazard+LLM model — the second option is especially valuable because it's a direct, visible readout of the project's core thesis (do the two approaches agree, and where do they diverge). Both are cheap to compute and meaningfully strengthen the dashboard's credibility.
- Experiment tracking via MLflow or Weights & Biases.

**Important framing:** if the LLM-augmented model performs no better than the baseline, that is a legitimate, honest, reportable finding — not a failure. Document it as such.

**Learn:** scikit-learn, XGBoost/LightGBM, cross-validation, SHAP, MLflow/W&B.
**Free resources:** scikit-learn docs, MLflow quickstart, SHAP documentation, Kaggle intermediate ML course.

### Stage 5: Geospatial Visualization + Deployment (Weeks 15–19) — the "masterclass" upgrade
- Weeks 15–16: Integrate Leaflet.js or Mapbox GL with district boundaries. **Use Prithvi (IBM/NASA's open-source geospatial foundation model, fine-tuned for flood detection) to generate flood extent masks from satellite imagery**, rather than DIY thresholding of raw bands — this is the current benchmark approach for this exact task and produces meaningfully more reliable results. **Precompute and cache these masks** for your chosen validation events rather than running inference live per request — live raster rendering/inference on demand is a real engineering trap to avoid given your fixed set of historical events.
- Week 17: Build the historical week selector — updates the map overlay, district ranking list, and snippet panel together as one reactive view.
- Week 18: Wire up clickable traceability — each district's score links to the specific report snippet(s) that drove it.
- Week 19: FastAPI backend, Docker containerization, deploy (Render/Railway/Streamlit Community Cloud), basic logging/monitoring.

**Learn:** Leaflet.js or Mapbox GL, Sentinel Hub/Google Earth Engine basics, FastAPI, Docker, GitHub Actions.
**Free resources:** FastAPI official tutorial, Docker "Get Started" guide, GitHub Actions docs.

### Cross-cutting: Software engineering quality (ongoing, Weeks 1–20)
These run alongside every stage, not as a separate phase — they're what make the project feel maintainable by a team rather than a one-off demo:

- **Unit tests** for critical components, especially data transformations and feature engineering logic — start writing these as each piece of Stage 1/3/4 code is built, not retroactively.
- **Integration tests** for the ingestion pipeline (Stage 1) — verifying the full raw-to-curated flow works end-to-end, not just individual functions.
- **Type hints and static checking** (mypy) across the codebase.
- **A reproducible configuration system** (YAML-based config files) so experiments — which event set, which model hyperparameters, which prompt version — can be rerun without touching code.
- **Clear versioning of datasets and models** — tag which GADM version, which data snapshot, and which trained model produced any given result, so any number in your final report is traceable back to exactly what produced it.

### Weeks 19–20: Polish & Documentation
- Architecture diagram, full README, `methodology.md` (decisions, tradeoffs, and the Stage 4 hypothesis/result stated honestly).
- Demo video walking through the week-selector/map/snippet interaction.
- GitHub cleanup: consistent formatting (`black`), meaningful commit history, `.env.example`, basic tests.

---

## 5. Repository structure

```
flood-impact-pipeline/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── .env.example
├── config/
│   └── (YAML experiment configs — event sets, hyperparameters, prompt versions)
├── data/
│   ├── raw/          (gitignored)
│   ├── staging/
│   └── curated/
├── src/
│   ├── ingestion/
│   ├── geo_resolution/   (location_mapping.py — GeoPy + manual dictionary)
│   ├── analysis/
│   ├── extraction/
│   ├── modeling/
│   └── api/
├── notebooks/
├── tests/
├── docs/
│   ├── architecture.md
│   └── methodology.md
├── evaluation/
│   └── results/
└── docker/
    └── Dockerfile
```

---

## 6. Cost breakdown

| Item | Cost |
|---|---|
| Compute (dev, training) | $0 (local + free Colab/Kaggle GPU quota) |
| LLM API calls | $0–$40 (or $0 using a local open-source model via Ollama) |
| Fine-tuning compute (stretch) | $0–$20 |
| Database | $0 (Supabase/Neon free tier) |
| Hosting/deployment | $0–$20 |
| Version control/CI | $0 (GitHub free tier) |
| Domain name (optional) | $10–15/year |
| Learning resources | $0–$40 |
| **Total** | **$0–$100 for the full 5 months** |

---

## 7. Skills you can honestly claim on completion

**Data Engineering:** ETL/ELT pipelines, PostgreSQL/SQL, orchestration (Airflow/Dagster), data quality validation, multi-source API integration, geospatial data handling.

**Data Analysis:** EDA, statistical reasoning, visualization, dashboarding, stakeholder-facing narrative writing.

**NLP/LLM Engineering:** prompt engineering, structured output extraction (Instructor/Outlines), building and rigorously evaluating an extraction pipeline (precision/recall/F1), optionally LoRA/QLoRA fine-tuning and prompting-vs-fine-tuning comparison.

**Machine Learning:** supervised classification, cross-validation, class imbalance handling, model interpretability (SHAP), experiment tracking, designing a fair comparative experiment (not just training one model).

**MLOps/Deployment:** API development (FastAPI), Docker, basic CI/CD, cloud deployment, monitoring/logging.

**Software Engineering discipline:** unit and integration testing, type hints and static analysis (mypy), reproducible configuration management (YAML-based experiment configs), dataset/model versioning — the skills that show you can build something a team could maintain, not just something that runs once.

**Higher-level, harder-to-teach skills:** end-to-end system ownership, working with real messy multi-source data, honest evaluation methodology, domain-adjacent judgment (can discuss real companies like Floodbase as reference points), technical writing.

**Resume bullet:**
> "Built an end-to-end flood impact assessment system combining hydrological data with LLM-extracted signals from humanitarian reports to predict regional aid priorities — validated against real historical floods across South and Southeast Asia; deployed as a live interactive dashboard."

---

## 8. Key risks and how they're handled

- **Spatial entity resolution failure** → solved explicitly in Stage 1, Week 3, before it can stall Stage 3.
- **LLM output not machine-readable** → solved via Instructor/Outlines instead of hoping for clean JSON.
- **No evaluation baseline** → hand-labeled ground truth set built in Stage 3, Week 9, before any "improvement" claims are made.
- **LoRA fine-tuning eating the schedule** → explicitly marked as strict stretch goal, first to cut.
- **Negative result in Stage 4** → pre-framed as a legitimate, honest scientific finding, not a failure.
- **Live satellite rendering overwhelming the backend** → solved by precomputing/caching static tiles for the fixed set of validation events instead of live queries.
- **Messy, unprofessional-looking repo** → solved via defined folder structure, `black` formatting, meaningful commits, and a `methodology.md` that documents real decision-making.
- **Administrative boundary drift** → one GADM version pinned for the entire project; newer/older place names manually mapped back to it.
- **Humanitarian jargon misread by the LLM** → WASH/NFI/IDP and similar acronyms explicitly defined in the system prompt and in the ground-truth labeling glossary.
- **Spatial/temporal leakage inflating model performance** → spatial block CV (and optionally temporal block CV) used instead of random train/test splits.
- **Class imbalance from mostly-zero-impact data** → peacetime weeks downsampled within each train/test block, not before splitting.
