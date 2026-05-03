"""Tests for aggregate.counts_for_clade against a tiny fixture sqlite DB."""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest

from taxonview import aggregate


@pytest.fixture
def fixture_db(tmp_path):
    db = tmp_path / "fixture.db"
    conn = sqlite3.connect(db)
    conn.execute("""
        CREATE TABLE taxid_features (
            taxid INTEGER PRIMARY KEY,
            short_read_count INTEGER NOT NULL DEFAULT 0,
            long_read_count INTEGER NOT NULL DEFAULT 0,
            assembly_count INTEGER NOT NULL DEFAULT 0,
            annotation_count INTEGER NOT NULL DEFAULT 0
        )
    """)
    # 4 species: 1001 has asm+ann, 1002 has asm only, 1003 has nothing,
    # 1004 has 3 asms and 1 ann.
    rows = [
        (1001, 0, 0, 2, 1),
        (1002, 0, 0, 1, 0),
        # 1003 absent → represents zero counts
        (1004, 0, 0, 3, 1),
    ]
    conn.executemany("INSERT INTO taxid_features VALUES (?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    return str(db)


def test_counts_for_clade_basic(fixture_db):
    descendants = [1001, 1002, 1003, 1004]
    with patch.object(aggregate, "descendant_species", return_value=descendants), \
         patch.object(aggregate, "get_name", return_value="FixtureClade"):
        with aggregate.open_db(fixture_db) as conn:
            counts = aggregate.counts_for_clade(conn, clade_taxid=999, rank="genus")

    assert counts.named_species == 4
    assert counts.species_with_assembly == 3
    assert counts.species_with_annotation == 2
    assert counts.total_assemblies == 6
    assert counts.total_annotations == 2
    assert counts.rank == "genus"
    assert counts.taxid == 999
    assert counts.name == "FixtureClade"


def test_counts_for_clade_empty(fixture_db):
    with patch.object(aggregate, "descendant_species", return_value=[]), \
         patch.object(aggregate, "get_name", return_value="Empty"):
        with aggregate.open_db(fixture_db) as conn:
            counts = aggregate.counts_for_clade(conn, clade_taxid=42, rank="class")
    assert counts.named_species == 0
    assert counts.species_with_assembly == 0
    assert counts.total_assemblies == 0


def test_chunked_above_999(fixture_db):
    """Chunking handles species lists larger than SQLite's bound-variable limit."""
    big = list(range(2000, 4000))  # 2000 taxids — none in DB → all zero
    with patch.object(aggregate, "descendant_species", return_value=big), \
         patch.object(aggregate, "get_name", return_value="Big"):
        with aggregate.open_db(fixture_db) as conn:
            counts = aggregate.counts_for_clade(conn, clade_taxid=1, rank="order")
    assert counts.named_species == 2000
    assert counts.species_with_assembly == 0
    assert counts.total_assemblies == 0
