"""Leads ledger: one CSV row per house, filled in by hand as reality happens.

The engine appends rows for new houses; Oscar (or a Claude session he tells)
fills in dropped/response columns. Stats are computed only from what's
actually logged — blank means unknown, never assumed.
"""

import csv
from pathlib import Path

COLUMNS = ["code", "photo_date", "flyer_date", "dropped_date",
           "response_date", "response_channel", "outcome", "notes"]


def _csv_path(campaign_dir: Path) -> Path:
    return campaign_dir / "leads.csv"


def _read(campaign_dir: Path) -> list[dict]:
    path = _csv_path(campaign_dir)
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def append_houses(campaign_dir: Path, houses: list[dict], run_date: str) -> None:
    path = _csv_path(campaign_dir)
    rows = _read(campaign_dir)
    existing = {r["code"] for r in rows}
    for h in houses:
        if h["code"] in existing:
            continue
        rows.append({c: "" for c in COLUMNS} | {
            "code": h["code"],
            "photo_date": h.get("photo_date", ""),
            "flyer_date": run_date if h.get("flyer") else "",
        })
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def stats(campaign_dir: Path, config: dict) -> dict:
    rows = _read(campaign_dir)
    dropped = [r for r in rows if r["dropped_date"].strip()]
    responses = [r for r in rows if r["response_date"].strip()]
    costs = config.get("costs_gbp", {})
    image_cost = costs.get("image_per_makeover")
    print_cost = costs.get("print_per_flyer")
    known_costs = image_cost is not None and print_cost is not None

    return {
        "houses_total": len(rows),
        "flyers_made": len([r for r in rows if r["flyer_date"].strip()]),
        "dropped": len(dropped),
        "responses": len(responses),
        "response_rate": (len(responses) / len(dropped)) if dropped else None,
        "cost_total_gbp": (
            round(len(rows) * image_cost + len(dropped) * print_cost, 2)
            if known_costs else None
        ),
        "note": None if known_costs else
                "cost unknown — fill costs_gbp in campaign.json",
    }
