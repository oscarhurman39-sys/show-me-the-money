#!/usr/bin/env python3
"""Overnight Engine orchestrator.

Usage:
  python3 engine/run.py [--campaign campaigns/garden-doordrop] [--mock]
  python3 engine/run.py stats [--campaign ...]
  python3 engine/run.py pitch [--campaign ...]

Default run: intake -> makeover -> flyer -> leads ledger -> batch PDF.
Prints a human summary and ends with one machine-readable JSON line
(prefix SUMMARY:) so a routine session can report it without parsing logs.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import flyer, intake, leads, pitch  # noqa: E402
from pipeline.makeover import MakeoverBlocked, run as run_makeover  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="process",
                        choices=["process", "stats", "pitch"])
    parser.add_argument("--campaign", default="campaigns/garden-doordrop")
    parser.add_argument("--mock", action="store_true",
                        help="placeholder makeovers, no API key needed")
    args = parser.parse_args()

    campaign_dir = Path(args.campaign).resolve()
    config = json.loads((campaign_dir / "campaign.json").read_text())
    run_date = date.today().isoformat()

    if args.command == "stats":
        print(json.dumps(leads.stats(campaign_dir, config), indent=2))
        return 0

    if args.command == "pitch":
        out = pitch.generate(campaign_dir, config, run_date)
        print(f"pitch pack written: {out}")
        return 0

    new = intake.scan(campaign_dir, run_date)
    print(f"[intake] {len(new)} new photo(s) registered")

    blocked, made_over = [], []
    for house in intake.pending_makeover(campaign_dir):
        out_path = campaign_dir / "out" / "makeovers" / f"{house['code']}_makeover"
        try:
            result = run_makeover(campaign_dir / house["original"], out_path,
                                  config["makeover_style"], mock=args.mock)
            house["makeover"] = str(result.relative_to(campaign_dir))
            if args.mock:
                house["makeover_is_mock"] = True
            made_over.append(house["code"])
            print(f"[makeover] {house['code']} -> {house['makeover']}"
                  + (" (MOCK)" if args.mock else ""))
        except MakeoverBlocked as e:
            blocked.append({"code": house["code"], "reason": str(e)})
            print(f"[makeover] {house['code']} BLOCKED: {e}")
        _update_house(campaign_dir, house)

    flyers = []
    for house in intake.pending_flyer(campaign_dir):
        pdf = flyer.render(house, campaign_dir, config)
        house["flyer"] = str(pdf.relative_to(campaign_dir))
        flyers.append(pdf)
        _update_house(campaign_dir, house)
        print(f"[flyer] {house['code']} -> {house['flyer']}")

    state = intake.load_state(campaign_dir)
    leads.append_houses(campaign_dir, list(state["houses"].values()), run_date)

    batch = flyer.merge_batch(flyers, campaign_dir, run_date)
    if batch:
        print(f"[batch] print-ready file: {batch.relative_to(campaign_dir)}")

    summary = {
        "date": run_date,
        "new_photos": len(new),
        "makeovers": made_over,
        "mock": args.mock,
        "flyers": [str(p.relative_to(campaign_dir)) for p in flyers],
        "batch_pdf": str(batch.relative_to(campaign_dir)) if batch else None,
        "blocked": blocked,
        "stats": leads.stats(campaign_dir, config),
    }
    print("SUMMARY:" + json.dumps(summary))
    return 0


def _update_house(campaign_dir: Path, house: dict) -> None:
    state = intake.load_state(campaign_dir)
    state["houses"][house["code"]] = house
    intake.save_state(campaign_dir, state)


if __name__ == "__main__":
    sys.exit(main())
