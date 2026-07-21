"""Pitch pack: a landscaper-facing one-pager built ONLY from logged reality.

Refuses to dress up missing data — unknowns are printed as unknowns.
The point of the doordrop test is to fill these numbers in; the pitch
becomes sellable the day they're real.
"""

from pathlib import Path

from . import leads


def generate(campaign_dir: Path, config: dict, run_date: str) -> Path:
    s = leads.stats(campaign_dir, config)
    rate = f"{s['response_rate'] * 100:.1f}%" if s["response_rate"] is not None else "no data yet"
    cost = f"£{s['cost_total_gbp']}" if s["cost_total_gbp"] is not None else "not yet known"

    ready = s["dropped"] > 0 and s["responses"] > 0
    status = (
        "READY TO PITCH — numbers below are real, logged results."
        if ready else
        "NOT READY TO PITCH — this is a template waiting for street-test data. "
        "Do not send it to a landscaper yet; unverified numbers burn trust."
    )

    body = f"""# Warm garden leads from {config.get('area', 'your area')}

> Status: {status}
> Generated {run_date} from leads.csv — nothing below is estimated or invented.

## What this is

We photograph front gardens, produce an AI visual of the same garden
professionally landscaped, and put it through the homeowner's door as a
printed flyer. Homeowners who respond have seen a picture of *their own
garden* transformed — they are warm, self-selected leads, not a cold list.

## The numbers so far

| Metric | Value |
|---|---|
| Flyers delivered | {s['dropped']} |
| Responses (quote requests) | {s['responses']} |
| Response rate | {rate} |
| Our cost to date | {cost} |

## The offer

- **Per lead:** you pay only for homeowners who responded — name, house,
  and the exact makeover image they responded to.
- **Per street (done-for-you):** flat fee per street, your branding on the
  envelope, every response goes straight to you.

Comparable spend: landscapers pay directories £150–500/month for
non-exclusive leads with no visual hook.

*Contact: {config.get('contact', {}).get('phone', '')}*
"""
    out = campaign_dir / "out" / "pitch" / "landscaper-pitch.md"
    out.write_text(body)
    return out
