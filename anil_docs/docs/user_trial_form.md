# Bot usability trial (target: 10 or more users, at least half Hindi speakers)

Give each participant 5 tasks on their own phone. Record in one row per participant.

Tasks: 1) start the bot and pick a language, 2) share location, 3) ask the current weather, 4) ask about flood risk, 5) ask for crop advice and subscribe to alerts.

CSV columns for `tools/trial_analysis.py`:
`participant,language,age_group,reply_seconds,clarity_1to5,hindi_quality_1to5,usefulness_1to5,trust_1to5,understood_advice_yes_no,comments`

Show every participant a sample RED alert and ask them in their own words what they would do; mark `understood_advice_yes_no` = yes only if they say they would follow the authorities and prepare to move, and understand it is advice not an order.

Also ask: "Does 'status unknown' make sense to you? Would you think it is safe?" - the correct understanding is *not safe, not confirmed*.

Consent: tell participants their answers are anonymous and used for a college project; do not record names or phone numbers.
Run: `python -m anil_docs.tools.trial_analysis responses.csv`
