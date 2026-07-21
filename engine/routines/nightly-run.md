# Nightly run — instructions for the scheduled session

You are a fresh Claude session fired by the "Doordrop nightly build" routine.
Follow exactly; keep cost near zero when there is nothing to do.

1. In `show-me-the-money`, fetch and check out branch
   `claude/passive-income-framework-jtw4vc`, then pull.
2. Check `campaigns/*/intake/` for files (ignore `.gitkeep`) and check
   `state.json` for houses with a missing/mock makeover while
   `MUAPIAPP_API_KEY` is now available.
   **If neither: reply "Nothing to process." and STOP. No installs, no
   commits.**
3. `pip install -r engine/requirements.txt` (also `pip install cffi` if pypdf
   import fails — known base-image quirk).
4. If `MUAPIAPP_API_KEY` is set in the environment: `python3 engine/run.py`.
   If not: `python3 engine/run.py --mock`, and your summary MUST open with
   "BLOCKED: no image API key — flyers are mock placeholders, do not print."
5. Read the `SUMMARY:` JSON line. Sanity-check one new flyer PDF exists and
   is ~1 page A5 (pypdf) before trusting it.
6. Improve nothing silently: if you refine flyer copy for a batch, edit
   `campaign.json` copy fields in the same commit so the change is visible.
7. Commit results (`processed/`, `out/`, `state.json`, `leads.csv`) with
   message `chore(doordrop): nightly batch <date> — <n> flyers` and push to
   the same branch (`git push -u origin claude/passive-income-framework-jtw4vc`,
   retry up to 4 times with 2s/4s/8s/16s backoff on network failure).
8. Final message = the summary Oscar sees on his phone: new flyers count,
   batch PDF path, blockers, and current stats line. Nothing else.

Reference for tone and format of the stats line: the `money-report` skill in
`skills/money-report/` (used for our own business per COMMERCIAL-LICENSE §1).
