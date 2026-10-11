# NASA POWER regional evidence snapshots

These CSV files are reproducible 2025 historical-climate snapshots used by the MausamSahayak Evidence Lab:

| File | Location | Coordinates | Period |
|---|---|---|---|
| `faridabad_nasa_power_2025.csv` | Faridabad | 28.4089 N, 77.3178 E | 2025-01-01 to 2025-12-31 |
| `delhi_nasa_power_2025.csv` | Delhi | 28.6139 N, 77.2090 E | 2025-01-01 to 2025-12-31 |
| `greater_noida_nasa_power_2025.csv` | Greater Noida | 28.4744 N, 77.5040 E | 2025-01-01 to 2025-12-31 |

Source: NASA POWER Daily Point API, agroclimatology community, local solar time. Parameters are `T2M`, `T2M_MIN`, `T2M_MAX`, `RH2M`, and `PRECTOTCORR`. Regenerate a snapshot with:

```bash
python -m parul_risk_crop.historical_weather OUTPUT.csv --lat LATITUDE --lon LONGITUDE
```

NASA POWER serves gridded data. These nearby NCR coordinates resolve to the same native grid cell and therefore have matching daily values. The files retain the requested city-level query provenance, but must not be presented as street-level observations or as a flood-warning source.
