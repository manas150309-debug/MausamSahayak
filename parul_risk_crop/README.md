# Parul - Risk rules and crop logic

| File | Role |
|---|---|
| `levels.py` | GREEN < UNKNOWN < YELLOW < ORANGE < RED (UNKNOWN deliberately above GREEN) |
| `risk_engine.py` | `assess_flood`, `assess_heat` - pure functions, tunable threshold dataclasses, structured reasons for translation |
| `crops_data.py`, `crop_advisor.py`, `data/district_normals.csv` | Rule-based crop advisor (v1) |
| `forecast.py` | Open-Meteo rainfall forecast with cache; failure returns None |
| `train_crop_model.py` | Random Forest crop model (v2), test accuracy + 5-fold CV |
| `validate_thresholds.py` | Precision / recall / false-alarm / miss rate and a threshold sweep on labelled history |
| `make_sample_history.py`, `make_sample_crop_data.py` | SYNTHETIC data generators so the pipelines run before real data exists |

## Flood rules in one table
| Level | Triggers (defaults in `FloodThresholds`) |
|---|---|
| UNKNOWN | no data for 30 min, rain or water-level value missing while the node is reporting |
| YELLOW | rain 24 h over 30 mm; rain 72 h at least 75 mm; level rising 3 cm/h or more; level at least 50 % of danger mark; heavy forecast; upstream rising |
| ORANGE | rain 24 h over 65 mm; 72 h at least 150 mm; 30 mm in one hour; level at least 70 % of danger and rising; rapid rise (10 cm/h); upstream surge |
| RED | level at or above danger mark; rise 30 cm/h or more (flash wave); rapid rise near danger; rapid rise + saturated soil + heavy forecast; 115.6 mm in 24 h on saturated soil; upstream surge near danger |

Every threshold is a starting value. **Your job**: get real history (`anil_docs/tools/fetch_historical_rain.py`), run `validate_thresholds.py --sweep`, choose thresholds, and report the trade-off.

## Real work still to do
1. Replace synthetic data with real data and report real metrics.
2. Get the crop ranges and district normals reviewed (Anil / KVK).
3. Train the ML model on a real public dataset and compare it with the rules.
