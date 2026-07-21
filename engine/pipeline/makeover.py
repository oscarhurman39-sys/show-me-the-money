"""Makeover: turn an original garden photo into an AI makeover image.

Providers:
  mock  — no network. Tints the original and stamps a banner so print layout
          can be tested for free before any API key exists.
  muapi — image-to-image edit via MuAPI nano-banana-edit. Call pattern taken
          from the working ai-real-estate-stager app (upload_file ->
          nano-banana-edit -> poll predictions/<id>/result). Needs
          MUAPIAPP_API_KEY in the environment.
"""

import os
import time
from pathlib import Path

import requests

MUAPI_BASE = "https://api.muapi.ai/api/v1"
POLL_INTERVAL_S = 4
POLL_MAX_ATTEMPTS = 45  # 3 minutes — headless batch, no reason to give up early


class MakeoverBlocked(Exception):
    """Raised when a makeover can't run (no key, API failure). Not a bug."""


def run(original: Path, out_path: Path, style_prompt: str, mock: bool) -> Path:
    if mock:
        return _mock(original, out_path)
    api_key = os.environ.get("MUAPIAPP_API_KEY", "").strip()
    if not api_key:
        raise MakeoverBlocked(
            "MUAPIAPP_API_KEY not set — real makeovers blocked. "
            "Run with --mock to test layout, or add the key to the environment."
        )
    return _muapi(original, out_path, style_prompt, api_key)


def _mock(original: Path, out_path: Path) -> Path:
    from PIL import Image, ImageDraw, ImageEnhance

    img = Image.open(original).convert("RGB")
    img = ImageEnhance.Color(img).enhance(1.5)
    overlay = Image.new("RGB", img.size, (40, 140, 60))
    img = Image.blend(img, overlay, 0.25)
    draw = ImageDraw.Draw(img)
    # banner across the vertical centre so object-fit cropping can't hide it
    banner_h = max(28, img.height // 12)
    top = (img.height - banner_h) // 2
    draw.rectangle([0, top, img.width, top + banner_h], fill=(180, 30, 30))
    draw.text((10, top + banner_h // 4), "MOCK MAKEOVER - layout test only", fill=(255, 255, 255))
    out = out_path.with_suffix(".jpg")
    img.save(out, quality=88)
    return out


def _muapi(original: Path, out_path: Path, style_prompt: str, api_key: str) -> Path:
    headers = {"x-api-key": api_key}

    with open(original, "rb") as f:
        up = requests.post(f"{MUAPI_BASE}/upload_file", headers=headers,
                           files={"file": (original.name, f)}, timeout=120)
    if not up.ok:
        raise MakeoverBlocked(f"MuAPI upload failed: HTTP {up.status_code} {up.text[:200]}")
    image_url = up.json().get("url") or up.json().get("file_url")
    if not image_url:
        raise MakeoverBlocked(f"MuAPI upload returned no url: {up.text[:200]}")

    submit = requests.post(
        f"{MUAPI_BASE}/nano-banana-edit", headers={**headers, "Content-Type": "application/json"},
        json={"prompt": style_prompt, "images_list": [image_url]}, timeout=60,
    )
    if not submit.ok:
        raise MakeoverBlocked(f"MuAPI submit failed: HTTP {submit.status_code} {submit.text[:200]}")
    request_id = submit.json().get("request_id")
    output_url = submit.json().get("output")

    if request_id and not output_url:
        for _ in range(POLL_MAX_ATTEMPTS):
            time.sleep(POLL_INTERVAL_S)
            poll = requests.get(f"{MUAPI_BASE}/predictions/{request_id}/result",
                                headers=headers, timeout=60)
            if not poll.ok:
                continue
            data = poll.json()
            state = data.get("status") or data.get("state")
            if state in ("completed", "succeeded"):
                outputs = data.get("outputs") or []
                output_url = outputs[0] if outputs else (
                    data.get("output") if isinstance(data.get("output"), str) else None
                )
                if output_url:
                    break
            elif state == "failed":
                raise MakeoverBlocked(f"MuAPI prediction failed: {data.get('error')}")
        else:
            raise MakeoverBlocked(f"MuAPI timed out after {POLL_MAX_ATTEMPTS * POLL_INTERVAL_S}s "
                                  f"(request_id={request_id})")

    if not output_url:
        raise MakeoverBlocked("MuAPI returned no output image")

    img = requests.get(output_url, timeout=120)
    if not img.ok:
        raise MakeoverBlocked(f"Could not download makeover: HTTP {img.status_code}")
    out = out_path.with_suffix(".jpg")
    out.write_bytes(img.content)
    return out
