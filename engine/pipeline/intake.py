"""Intake: register new photos dropped into <campaign>/intake/.

Each photo gets a sequential house code (H001, H002, ...) and is moved to
processed/<code>_original.<ext>. State lives in <campaign>/state.json.
"""

import json
import shutil
from pathlib import Path

ACCEPTED = {".jpg", ".jpeg", ".png", ".webp"}


def load_state(campaign_dir: Path) -> dict:
    state_file = campaign_dir / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"next_house_num": 1, "houses": {}}


def save_state(campaign_dir: Path, state: dict) -> None:
    (campaign_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n")


def scan(campaign_dir: Path, run_date: str) -> list[dict]:
    """Move new intake photos into processed/, register them, return new houses."""
    state = load_state(campaign_dir)
    intake_dir = campaign_dir / "intake"
    processed_dir = campaign_dir / "processed"
    new_houses = []

    skipped = []
    for photo in sorted(intake_dir.iterdir()):
        if photo.name.startswith("."):
            continue
        if photo.suffix.lower() not in ACCEPTED:
            skipped.append(photo.name)
            continue
        code = f"H{state['next_house_num']:03d}"
        state["next_house_num"] += 1
        dest = processed_dir / f"{code}_original{photo.suffix.lower()}"
        shutil.move(str(photo), str(dest))
        house = {
            "code": code,
            "original": str(dest.relative_to(campaign_dir)),
            "photo_date": run_date,
            "makeover": None,
            "flyer": None,
        }
        state["houses"][code] = house
        new_houses.append(house)

    save_state(campaign_dir, state)
    if skipped:
        print(f"[intake] skipped unsupported files (use jpg/png/webp): {skipped}")
    return new_houses


def pending_makeover(campaign_dir: Path) -> list[dict]:
    """Houses registered but with no makeover yet (e.g. earlier run was blocked)."""
    state = load_state(campaign_dir)
    return [h for h in state["houses"].values() if not h.get("makeover")]


def pending_flyer(campaign_dir: Path) -> list[dict]:
    state = load_state(campaign_dir)
    return [h for h in state["houses"].values() if h.get("makeover") and not h.get("flyer")]
