# Data sources (verify access, licence and update frequency before relying on any)

| Need | Source | How we use it | Status / what to verify |
|---|---|---|---|
| Rainfall forecast | Open-Meteo forecast API (`api.open-meteo.com`) | `parul_risk_crop/forecast.py` sums next 24 h / 72 h rain per node | Built and unit-tested with mocked responses. Check the free-tier terms for your use |
| Historical rain | Open-Meteo archive API | `anil_docs/tools/fetch_historical_rain.py` | Reanalysis, smooths local extremes |
| Official warnings and district rainfall | IMD (mausam.imd.gov.in) | Manual reference; district normals for `district_normals.csv` | Replace the placeholder normals with IMD district values |
| River stage / forecast stations | CWC flood forecasting (cwc.gov.in), India-WRIS (indiawris.gov.in) | Historical river levels and danger marks for validation; danger mark for each node site | No simple public API assumed - download manually or request from the CWC / state water resources office |
| Alerts feed | NDMA SACHET (CAP alerts) | Possible future: show official alerts next to ours | Check whether a public feed is available |
| State flood reports | State disaster management authority (e.g. ASDMA for Assam, HSDMA for Haryana) | Flood event dates for labelling; contacts for the pilot | Ask for event lists in writing |
| Crop training data | Public crop-recommendation dataset (e.g. Kaggle "Crop Recommendation Dataset"); ICRISAT district-level data | `parul_risk_crop/train_crop_model.py` | Download yourself; cite the licence |
| Crop review | Local KVK (ICAR) / district agriculture office | `docs/kvk_validation_form.md` | Book a meeting in week 2 |
| Satellite rain (optional) | NASA GPM IMERG, CHIRPS | Cross-check rain gauge | Optional |

Rules for the report: cite every dataset with access date; keep a `data/README` listing file, source URL, date downloaded and licence; never present synthetic files (`*_SYNTHETIC.csv`) as results.
