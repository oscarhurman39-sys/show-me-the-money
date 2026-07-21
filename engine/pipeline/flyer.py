"""Flyer: render a print-ready A5 PDF per house from templates/flyer.html.

Images are embedded as base64 data URIs (no file:// permission issues),
QR codes come from segno, and HTML -> PDF uses the pre-installed Chromium.
New flyers are also merged into one batch PDF for a single print-shop upload.
"""

import base64
import subprocess
import tempfile
from pathlib import Path

import segno

CHROMIUM = "/opt/pw-browsers/chromium"
TEMPLATE = Path(__file__).parent.parent / "templates" / "flyer.html"


def _data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _qr_data_uri(url: str) -> str:
    return segno.make(url, error="m").svg_data_uri(scale=4, dark="#1d2b1f")


def render(house: dict, campaign_dir: Path, config: dict) -> Path:
    copy = config["copy"]
    contact = config["contact"]
    response_url = contact.get("response_url", "")
    qr_target = (
        f"{response_url}{'&' if '?' in response_url else '?'}h={house['code']}"
        if response_url and not response_url.startswith("SET ME")
        else f"tel:{contact.get('phone', '')}"
    )

    html = TEMPLATE.read_text()
    for key, value in {
        "{{HEADLINE}}": copy["headline"],
        "{{SUBHEAD}}": copy["subhead"],
        "{{BODY}}": copy["body"],
        "{{CTA}}": copy["cta"],
        "{{PHONE}}": contact.get("phone", ""),
        "{{CODE}}": house["code"],
        "{{BEFORE_SRC}}": _data_uri(campaign_dir / house["original"]),
        "{{AFTER_SRC}}": _data_uri(campaign_dir / house["makeover"]),
        "{{QR_SRC}}": _qr_data_uri(qr_target),
    }.items():
        html = html.replace(key, value)

    out_pdf = campaign_dir / "out" / "flyers" / f"{house['code']}_flyer.pdf"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        tmp_html = f.name

    result = subprocess.run(
        [CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", tmp_html],
        capture_output=True, text=True, timeout=120,
    )
    Path(tmp_html).unlink(missing_ok=True)
    if result.returncode != 0 or not out_pdf.exists():
        raise RuntimeError(f"Chromium PDF render failed: {result.stderr[-400:]}")
    return out_pdf


def merge_batch(pdfs: list[Path], campaign_dir: Path, run_date: str) -> Path | None:
    if not pdfs:
        return None
    from pypdf import PdfWriter

    out = campaign_dir / "out" / "flyers" / f"batch_{run_date}.pdf"
    writer = PdfWriter()
    for pdf in pdfs:
        writer.append(str(pdf))
    with open(out, "wb") as f:
        writer.write(f)
    return out
