# Weekly digest — instructions for the scheduled session

You are a fresh Claude session fired by the "Doordrop weekly digest" routine,
Sunday evenings.

1. In `show-me-the-money`, fetch and check out branch
   `claude/passive-income-framework-jtw4vc`, then pull.
2. `pip install -r engine/requirements.txt` (plus `cffi` if pypdf fails),
   then `python3 engine/run.py stats`.
3. If houses_total is 0 and nothing changed since last week: reply
   "No activity this week." and STOP.
4. Otherwise `python3 engine/run.py pitch` to regenerate the pitch pack,
   commit it, push (same branch, same retry rule as the nightly run).
5. Final message, in this order, plain language (`money-report` skill in
   `skills/money-report/` is the format reference):
   - The numbers: flyers made / dropped / responses / response rate / costs.
     Unknown = say "unknown", never estimate.
   - One sentence on what the numbers mean for the street test.
   - The single next brick from `LEDGER.md` — quote it verbatim. If the
     ledger's active brick looks done per the data, say so and suggest ONE
     replacement brick (phone-sized, concrete, binary). Do not write plans.
6. Never invent responses, never mark `dropped_date` yourself — only Oscar
   logs reality in `leads.csv`.
