# Test plan (run before 24 Oct feature freeze and again before the final demo)

Automated: `python -m unittest discover -s . -t . -p "test_*.py"` must pass (see repo README for the count).

| ID | Test | Steps | Expected |
|---|---|---|---|
| T-01 | Normal reading | Node publishes normal data | Dashboard GREEN, bot shows temperature/humidity |
| T-02 | Heavy rain | Simulator `heavy_rain` or watering can on gauge | Rain 24 h rises; level YELLOW/ORANGE |
| T-03 | Flood | Simulator `flood`, or raise water in a tank under the ultrasonic sensor | RED alert; subscribed test phone gets Telegram + SMS (dry-run log if no SMS provider) |
| T-04 | Silent node | Power off node | After 30 min: UNKNOWN, alert "station not reporting", never GREEN |
| T-05 | Sensor fault | Unplug ultrasonic sensor | Water-level null -> UNKNOWN with reason "water-level sensor not reporting" |
| T-06 | Offline buffering | Turn Wi-Fi off 1 h, on again | Buffered readings arrive, no duplicates |
| T-07 | Bad data | POST temperature 999 | Stored as null, field listed in `dropped_fields` |
| T-08 | Forecast down | Block internet to forecast host | Monitoring continues, no crash |
| T-09 | Hindi flow | Whole conversation in Hindi | Correct text, RED text mentions advisory, 112 and 1078 |
| T-10 | Far user | Share a location 100 km away | Bot says no reliable local station |
| T-11 | API down | Stop the backend | Bot replies with "cannot reach server" and points to IMD/authorities |
| T-12 | Upstream surge | Two nodes with `upstream_node_id`; raise upstream level fast | Downstream goes ORANGE with reason "upstream station..." before its own level moves |
| T-13 | Unsubscribe | `/unsubscribe`, trigger alert | No message |
| T-14 | Restart | Reboot server and bot | Data persists; bot does not replay old alerts |
