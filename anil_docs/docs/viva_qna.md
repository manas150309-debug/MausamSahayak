# Viva preparation - likely questions and honest answers

**Did IMD fail in the Assam floods?**
The sources we read say IMD recorded the upstream rainfall and said it was not a cloudburst. The gap was basin-specific, fast, last-mile warning for small rivers - not measurement of rainfall. We cannot claim a specific IMD warning was missing without a source.

**Do you solve the Assam flood problem?**
No. We built a low-cost pilot that addresses part of it: local river-stage sensing, a rule for sudden rises, upstream-to-downstream early warning, fail-safe handling of dead sensors, and vernacular delivery. Basin-wide coverage needs many nodes and official partnership.

**Why not just use the IMD/CWC data?**
We do use forecasts. They do not give stage at our exact village drain or a rise-rate alert with a dead-sensor fail-safe.

**What if your sensor dies during a flood?**
The station becomes UNKNOWN after 30 minutes and an alert says "not reporting - not safe". Last-known dangerous values still count.

**How did you choose thresholds? Are they right?**
Starting values based on IMD rainfall classes; tuned on historical data with a precision/recall trade-off table. They must be recalibrated per site.

**Is your crop advisor machine learning?**
Version 1 is rules from crop requirement ranges reviewed by a KVK. Version 2 is a Random Forest on a public dataset using only temperature, humidity and rainfall. We report both accuracies separately.

**What if the alert is wrong?**
False alarms reduce trust; misses can hurt. We show reasons with each alert, use advisory language, defer to authorities, and report the false-alarm ratio.

**Which parts are untested?**
Say clearly which parts ran on real hardware/bot token and which only in simulation (see repo README status table).

**What did each person do?**
Manas: backend. Parul: risk and crop logic. Nishant: sensors and firmware. Swati: bot. Anil: data, field work, validation, documents.
