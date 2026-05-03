"""TaxonView CLI: taxid → HTML radial visualisation."""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

from .aggregate import counts_for_clade, open_db
from .render import render
from .taxonomy import get_name, get_rank, resolve_lineage

DEFAULT_RANKS = ["species", "genus", "family", "order", "class"]


def _autodetect_db() -> str | None:
    """Look for euka_survey's features DB in common locations."""
    candidates = []
    here = Path(__file__).resolve()
    # Sibling repo: ../../../../euka_survey from src/taxonview/cli.py
    for up in (3, 4, 5):
        candidates.append(here.parents[up - 1] / "euka_survey")
    candidates.append(Path.cwd().parent / "euka_survey")
    candidates.append(Path.cwd() / "euka_survey")

    for base in candidates:
        if base.is_dir():
            matches = sorted(glob.glob(str(base / "eukaryote_taxid_features_*.db")))
            if matches:
                return matches[-1]  # newest by lexicographic date suffix
    return None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="taxonview",
        description="Visualise genomic resources across the taxonomic hierarchy of a focus species.",
    )
    p.add_argument("taxid", type=int, help="NCBI taxid of the focus species.")
    p.add_argument("--db", help="Path to euka_survey features SQLite DB. "
                                "Auto-detected if a sibling euka_survey/ exists.")
    p.add_argument("-o", "--out", help="Output HTML path. Default: taxonview_<taxid>.html")
    p.add_argument("--scale", choices=["log", "linear"], default="log",
                   help="Radius scaling for named-species count (default: log).")
    p.add_argument("--ranks", default=",".join(DEFAULT_RANKS),
                   help=f"Comma-separated ranks, innermost-first. Default: {','.join(DEFAULT_RANKS)}")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    db_path = args.db or _autodetect_db()
    if not db_path:
        print("Error: --db not provided and no euka_survey DB auto-detected.\n"
              "Pass --db /path/to/eukaryote_taxid_features_*.db", file=sys.stderr)
        return 2
    if not os.path.exists(db_path):
        print(f"Error: DB not found: {db_path}", file=sys.stderr)
        return 2

    focus_rank = get_rank(args.taxid)
    focus_name = get_name(args.taxid)
    if focus_rank != "species":
        print(f"Error: input taxid {args.taxid} ({focus_name}) has rank "
              f"'{focus_rank}', expected 'species'.", file=sys.stderr)
        return 2

    ranks = [r.strip() for r in args.ranks.split(",") if r.strip()]
    lineage = resolve_lineage(args.taxid, ranks)

    if "species" in ranks and "species" not in lineage:
        # ete3 lineage usually includes the focus; this guards rare edge cases.
        lineage["species"] = (args.taxid, focus_name)

    print(f"Focus: {focus_name} (taxid {args.taxid}, rank species)", file=sys.stderr)
    print(f"DB: {db_path}", file=sys.stderr)

    rings = []
    with open_db(db_path) as conn:
        for rank in ranks:
            if rank not in lineage:
                print(f"  - {rank}: not present in lineage; skipping", file=sys.stderr)
                continue
            tid, name = lineage[rank]
            print(f"  - {rank}: {name} (taxid {tid}) ...", file=sys.stderr, end=" ", flush=True)
            counts = counts_for_clade(conn, tid, rank)
            rings.append(counts)
            print(f"{counts.named_species} species, "
                  f"{counts.species_with_assembly} w/asm, "
                  f"{counts.species_with_annotation} w/ann", file=sys.stderr)

    out_path = args.out or f"taxonview_{args.taxid}.html"
    written = render(
        input_taxid=args.taxid,
        input_name=focus_name,
        rings=rings,
        scale=args.scale,
        out_path=out_path,
    )
    print(f"Wrote {written}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
