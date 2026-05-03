"""NCBI taxonomy lookups: lineage walking and descendant-species expansion.

Backed by ete3's local taxonomy SQLite (auto-managed in ~/.etetoolkit/).
"""

from __future__ import annotations

import sqlite3
from functools import lru_cache

from ete3 import NCBITaxa

# Same set used by euka_survey/scripts/ete_utils.py — anything that "is a species
# at the leaf level" should count, including subspecies/varietas/forma/strain.
SPECIES_LEVEL_RANKS = ("species", "subspecies", "varietas", "forma", "strain")


@lru_cache(maxsize=1)
def _ncbi() -> NCBITaxa:
    return NCBITaxa()


def get_name(taxid: int) -> str:
    names = _ncbi().get_taxid_translator([taxid])
    return names.get(taxid, "Unknown")


def get_rank(taxid: int) -> str:
    ranks = _ncbi().get_rank([taxid])
    return ranks.get(taxid, "unknown")


def resolve_lineage(taxid: int, ranks: list[str]) -> dict[str, tuple[int, str]]:
    """For a focus taxid, return {rank: (taxid, name)} for each requested rank.

    The focus taxid itself appears under its own rank (e.g. "species") if that
    rank is requested. Ancestor ranks come from `get_lineage`. Missing ranks
    (e.g. when a clade has no formal "class") are simply omitted.
    """
    ncbi = _ncbi()
    lineage = ncbi.get_lineage(taxid) or []
    rank_of = ncbi.get_rank(lineage)
    name_of = ncbi.get_taxid_translator(lineage)

    wanted = set(ranks)
    out: dict[str, tuple[int, str]] = {}
    for tid in lineage:
        r = rank_of.get(tid)
        if r in wanted and r not in out:
            out[r] = (tid, name_of.get(tid, "Unknown"))
    return out


def descendant_species(taxid: int) -> list[int]:
    """All descendant taxids classified as a species-level rank.

    Uses a recursive CTE against ete3's taxonomy DB — same pattern as
    euka_survey/scripts/ete_utils.py:get_species_and_subspecies.
    """
    ncbi = _ncbi()
    placeholders = ", ".join("?" * len(SPECIES_LEVEL_RANKS))
    query = f"""
        WITH RECURSIVE subtree(taxid) AS (
            SELECT taxid FROM species WHERE taxid = ?
            UNION ALL
            SELECT s.taxid FROM species AS s
            JOIN subtree AS t ON s.parent = t.taxid
        )
        SELECT s.taxid FROM subtree AS t
        JOIN species AS s ON s.taxid = t.taxid
        WHERE s.rank IN ({placeholders})
    """
    conn = sqlite3.connect(ncbi.dbfile)
    try:
        return [row[0] for row in conn.execute(query, [taxid, *SPECIES_LEVEL_RANKS])]
    finally:
        conn.close()
