# Evaluation plan - every number you will put in the report

| Metric | How to measure | Script / tool | Target to aim for |
|---|---|---|---|
| Sensor accuracy (temp, RH, rain, level) | Compare with reference instruments, see `nishant_firmware/docs/calibration.md` | spreadsheet | report MAE and max error |
| Data delivery rate | received / expected readings per node per day (expected = 288) | SQL: `SELECT COUNT(*) FROM readings WHERE node_id=? AND ts>?` | above 95 % |
| Latency sensor -> database | `received_at - ts` in the `readings` table | SQL | median under 30 s |
| Latency database -> phone | time from alert row to Telegram message | bot logs | under 2 min (worker interval is 60 s) |
| Alert precision, recall, false-alarm ratio | `python -m parul_risk_crop.validate_thresholds history_real.csv --sweep` on REAL labelled data | Parul | report the trade-off table, not a single number |
| Stale-sensor detection | unplug a node, time until UNKNOWN alert | manual test T-04 | within 30 min + one worker cycle |
| Crop recommendation accuracy | (a) model: `train_crop_model.py` test and 5-fold CV on the public dataset; (b) rules: KVK agreement | Parul, Anil | report both, and say the rules are not ML |
| Bot usability | user trial | `tools/trial_analysis.py` | mean clarity 4 or above |
| Battery / solar | 3-day voltage log | logging | never below 3.5 V |

Honesty rules for the report
- Synthetic files in the repo (`*_SYNTHETIC.csv`) exist only to test code. Never quote their metrics.
- If there is no real flood during the field run, say so and rely on historical validation plus the simulated rain demo.
- Reanalysis rainfall (Open-Meteo archive) is smoother than gauge data: state that recall may be optimistic.
