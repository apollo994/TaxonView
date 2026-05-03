"""Aggregate genomic-resource counts for a clade from euka_survey's SQLite DB."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict

from .taxonomy import descendant_species, get_name

# SQLite default bound-variable limit is 999. 500 mirrors euka_survey/query_clade.py.
_CHUNK_SIZE = 500


@dataclass
class CladeCounts:
    rank: str
    taxid: int
    name: str
    named_species: int
    species_with_assembly: int
    species_with_annotation: int
    total_assemblies: int
    total_annotations: int

    def to_dict(self) -> dict:
        return asdict(self)


def _query_chunked(conn: sqlite3.Connection, taxids: list[int]) -> tuple[int, int, int, int]:
    """Return (species_with_assembly, species_with_annotation, total_assemblies, total_annotations)."""
    s_asm = s_ann = t_asm = t_ann = 0
    if not taxids:
        return 0, 0, 0, 0

    cur = conn.cursor()
    for start in range(0, len(taxids), _CHUNK_SIZE):
        chunk = taxids[start:start + _CHUNK_SIZE]
        placeholders = ",".join("?" * len(chunk))
        sql = f"""
            SELECT
                SUM(CASE WHEN assembly_count   > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN annotation_count > 0 THEN 1 ELSE 0 END),
                SUM(assembly_count),
                SUM(annotation_count)
            FROM taxid_features
            WHERE taxid IN ({placeholders})
        """
        row = cur.execute(sql, chunk).fetchone()
        if row:
            s_asm += row[0] or 0
            s_ann += row[1] or 0
            t_asm += row[2] or 0
            t_ann += row[3] or 0
    return s_asm, s_ann, t_asm, t_ann


def counts_for_clade(conn: sqlite3.Connection, clade_taxid: int, rank: str) -> CladeCounts:
    """Compute counts for the clade rooted at `clade_taxid`."""
    species = descendant_species(clade_taxid)
    s_asm, s_ann, t_asm, t_ann = _query_chunked(conn, species)
    return CladeCounts(
        rank=rank,
        taxid=clade_taxid,
        name=get_name(clade_taxid),
        named_species=len(species),
        species_with_assembly=s_asm,
        species_with_annotation=s_ann,
        total_assemblies=t_asm,
        total_annotations=t_ann,
    )


def open_db(path: str) -> sqlite3.Connection:
    """Open the euka_survey features DB read-only."""
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)
