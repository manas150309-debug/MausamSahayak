# Case study: the 2026 Upper Assam floods - what a hyperlocal system can and cannot fix

## 1. What was reported (as of the sources below; figures are provisional)
- Two flood waves: about 28 June 2026 (22,000+ people, six districts) and 18-21 July 2026 (16 districts, 794 villages) [World Weather Attribution].
- IMD attributed the July floods to heavy rainfall upstream (Aboi, Mon district, Nagaland: 137 mm on 19 July) and said the event did **not** meet its cloudburst definition (100 mm or more in an hour over roughly 20-30 sq km) [Assam University report; eKuhipath summary].
- Some experts described the Dikhow river event as resembling a landslide / debris-dam outburst: more than 60 landslides were reported in Mon district and the river went from warning level to danger level to its highest level within a few hours [SPMIAS analysis - a coaching-institute source, treat as one interpretation].
- Commentary calls for basin-specific forecasting instead of general rainfall alerts for the Assam-Nagaland border region, and for monitoring landslide blockages [Assam Tribune opinion, 18 Aug 2026].
- CWC issues flood forecasts for major rivers; earlier government documentation notes that river-level forecasts do not tell villages where flooding will occur, and one 2026 explainer says many CWC telemetry stations are non-functional because of poor maintenance, calibration gaps and vandalism [DARPG FLEWS document; Drishti IAS].

## 2. Be careful with the claim "the Met Department did not capture it"
The sources above say IMD **did record and describe** the rainfall. The gap they point to is different:
1. rain measured at a few points is not a warning for a specific small river and village,
2. river-stage forecasting is CWC's job and covers major rivers/stations, not every tributary,
3. a sudden wave from a landslide dam breach is not visible in rainfall totals at all, and
4. warnings must reach people in time, in a language and channel they use.

So in the viva say: *"the rainfall was recorded; what was missing was hyperlocal, basin-specific, fast, last-mile warning."* Do not say IMD "failed" unless you have a source showing that a specific warning was missing or late for the Dikhow basin. Search ASDMA / IMD bulletins for 17-20 July 2026 and cite exactly what was issued.

## 3. Which gaps our system addresses (and how far)
| Gap | What MausamSahayak does | Limit - say this honestly |
|---|---|---|
| Rain at a point, not the river | Water-level sensor on the small river/drain, checked against a per-site danger mark | Only where a node is installed |
| Sudden waves (landslide-dam breach, dam release) | `flash_rise` rule: RED if level rises 30 cm/h or more even far below danger; `upstream_surge` rules warn a downstream node from an upstream node | Lead time = travel time between nodes; measure it. Cannot see a blockage nobody instruments |
| Telemetry that silently stops | A silent or faulty sensor becomes UNKNOWN (never "all clear") and triggers an alert | Detects failure, does not fix it - needs maintenance |
| Warnings not reaching people | Telegram alerts in Hindi/English, SMS for RED, advisory wording that defers to authorities | **No Assamese yet**; Telegram needs data; SMS is only for users who registered a number |
| Advice unrelated to local conditions | Crop rules use local temperature, soil moisture and district rainfall normals | Not a forecast; needs KVK review |

## 4. What we do NOT solve
- We do not replace IMD or CWC and never issue evacuation orders.
- Two or three nodes cannot cover a 4,000+ sq km basin. Present the project as a **pilot for a village/sub-basin** and as a design others can replicate cheaply.
- Thresholds in this repo are calibrated for demo data (Faridabad, Haryana). For Assam they must be re-tuned on local rainfall and river data (use `fetch_historical_rain.py` + `validate_thresholds.py`).
- Assamese/Bodo language support needs native translators; the i18n layer (`swati_bot/i18n.py`) is built so a third language is one more dictionary plus review.

## 5. Suggested pilot extension for Assam (future work slide)
Nodes at two points on one tributary (upstream in the hills, downstream near a village), LoRa or GSM backhaul, `upstream_node_id` set in the backend, Assamese strings added, alert recipients agreed with the district administration / ASDMA.

## Sources (open and read them yourself before citing)
- Assam University, "Report: Flood 2026 Assam", Aug 2026 - https://www.aus.ac.in/wp-content/uploads/2026/08/Report_Flood_2026_Assam-University.pdf
- World Weather Attribution, "Flood impacts in Assam driven by high exposure and structural vulnerability..." - https://www.worldweatherattribution.org/flood-impacts-in-assam-driven-by-high-exposure-and-structural-vulnerability-amid-uncertain-rainfall-trends/
- Assam Tribune, "Turning upstream rainfall into early flood warning for Assam" - https://assamtribune.com/opinion/turning-upstream-rainfall-into-early-flood-warning-for-assam-1615752
- Drishti IAS, "Assam Floods and Flood Management in India" - https://www.drishtiias.com/daily-updates/daily-news-analysis/assam-floods-and-flood-management-in-india
- SPMIAS Academy, "Assam Flood 2026" - https://spmiasacademy.com/assam-flood-2026-causes-impact-guwahati/
- eKuhipath, "Assam Floods 2026" - https://www.ekuhipath.com/blog/assam-floods-2026-causes-impacts-challenges-the-road-ahead-complete-apscupsc-guide-24-07-2026
- CWC flood forecasting network page - https://cwc.gov.in/en/flood-forecasting-hydrological-observation
- Assam flood early-warning documentation (DARPG) - https://darpg.gov.in/sites/default/files/70.%20Flood%20Early%20Warning%20SystemFLEWS-Documentation-Final.pdf
