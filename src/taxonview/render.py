"""Render a TaxonView HTML report from a list of CladeCounts."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .aggregate import CladeCounts


def _env() -> Environment:
    return Environment(
        loader=PackageLoader("taxonview", "templates"),
        autoescape=select_autoescape(["html"]),
    )


def _load_d3() -> str:
    return resources.files("taxonview.templates").joinpath("d3.v7.min.js").read_text()


def render(
    *,
    input_taxid: int,
    input_name: str,
    rings: list[CladeCounts],
    scale: str,
    out_path: str | Path,
) -> Path:
    """Render rings (ordered species → class, innermost → outermost) to HTML."""
    payload = {
        "input_taxid": input_taxid,
        "input_name": input_name,
        "scale": scale,
        "rings": [r.to_dict() for r in rings],
    }
    template = _env().get_template("taxonview.html.j2")
    html = template.render(
        payload_json=json.dumps(payload, ensure_ascii=False),
        d3_source=_load_d3(),
        title=f"TaxonView — {input_name} ({input_taxid})",
    )
    out = Path(out_path)
    out.write_text(html, encoding="utf-8")
    return out
