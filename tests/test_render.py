"""Smoke test the renderer produces valid HTML with embedded data."""

from __future__ import annotations

import json
import re

from taxonview.aggregate import CladeCounts
from taxonview.render import render


def test_render_writes_html(tmp_path):
    rings = [
        CladeCounts(rank="species", taxid=9606, name="Homo sapiens",
                    named_species=1, species_with_assembly=1, species_with_annotation=1,
                    total_assemblies=5, total_annotations=3),
        CladeCounts(rank="genus", taxid=9605, name="Homo",
                    named_species=12, species_with_assembly=2, species_with_annotation=1,
                    total_assemblies=8, total_annotations=4),
    ]
    out = tmp_path / "out.html"
    written = render(input_taxid=9606, input_name="Homo sapiens",
                     rings=rings, scale="log", out_path=out)

    html = written.read_text()
    assert "<svg id=\"viz\"" in html
    # D3 should be inlined
    assert "d3 = " in html or "d3=" in html or "function(global" in html

    # Embedded JSON payload round-trips
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
    assert m
    data = json.loads(m.group(1))
    assert data["input_taxid"] == 9606
    assert len(data["rings"]) == 2
    assert data["rings"][0]["rank"] == "species"
