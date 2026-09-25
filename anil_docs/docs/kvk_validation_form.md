# Crop-advice validation form (for the KVK / agriculture officer)

Reviewer name / KVK / date: ____________________  District: ____________

Context to give the reviewer: MausamSahayak suggests crops from the local season, mean temperature, soil moisture and expected seasonal rainfall. Ranges are in `parul_risk_crop/crops_data.py`; district rainfall normals in `parul_risk_crop/data/district_normals.csv`.

## Part A - are the crop ranges reasonable? (edit the table directly)
For each crop please confirm or correct: sowing season, temperature range, rainfall range.

## Part B - test cases
Give the reviewer 8-10 realistic situations. The reviewer writes the crops they would recommend; Anil compares with the top 3 from the system.

| # | Season | Mean temp (C) | Seasonal rain (mm) | Soil moisture (%) | Irrigated? | Reviewer's crops | System top 3 | Agreement (0-3 matches) |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |

Agreement metric for the report: fraction of system top-3 crops that the reviewer also lists, averaged over cases. Also record disagreements and why (soil type, water, market, seed availability).

## Part C - safety review
- Any crop suggested that would be harmful or clearly wrong for the area? ____________
- Is the wording clear for a farmer? ____________
- Signature: ____________
