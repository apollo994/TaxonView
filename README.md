# TaxonView

Visualise the genomic resources available across the taxonomic hierarchy of a focus species.

Given an NCBI species taxid, TaxonView walks the lineage (species → genus → family → order → class → phylum) and, for each rank, asks the [euka_survey](https://github.com/Cobos-Bioinfo/euka_survey) database three questions:

- How many named species live in this clade?
- How many of them have at least one genome assembly?
- How many have at least one annotation?

It writes a single self-contained HTML file with a D3.js radial visualisation: concentric circles, one per rank, with circle radius proportional to named-species count and a wedge/sub-arc encoding the assembly and annotation fractions.

## Install

Requires Python ≥ 3.11 and the [euka_survey](https://github.com/Cobos-Bioinfo/euka_survey) features SQLite DB on disk (e.g. `eukaryote_taxid_features_2026_04_13.db`). The expected layout is TaxonView and euka_survey as siblings:

```
work/repo/
├── TaxonView/
└── euka_survey/   # contains eukaryote_taxid_features_*.db
```

Install in a venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The first run downloads NCBI taxdump (~50 MB) into `~/.etetoolkit/` via ete3.

## Usage

```bash
taxonview <species_taxid>
```

Example — *Heliconius melpomene*:

```bash
taxonview 34740 -o heliconius.html
```

Stderr shows what was queried; the HTML is written to the output path.

```
Focus: Heliconius melpomene (taxid 34740, rank species)
  - species: Heliconius melpomene ... 29 species, 15 w/asm, 0 w/ann
  - genus:   Heliconius           ... 209 species, 84 w/asm, 0 w/ann
  - family:  Nymphalidae          ... 7949 species, 294 w/asm, 101 w/ann
  - order:   Lepidoptera          ... 134771 species, 2252 w/asm, 715 w/ann
  - class:   Insecta              ... 743530 species, 5306 w/asm, 1582 w/ann
```

Open the resulting HTML in any browser. Hover any ring for full counts.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--db PATH` | auto-detect sibling `euka_survey/eukaryote_taxid_features_*.db` | path to euka_survey SQLite DB |
| `-o, --out PATH` | `taxonview_<taxid>.html` | output HTML path |
| `--scale {log,linear}` | `log` | radius scaling for named-species count |
| `--ranks RANKS` | `species,genus,family,order,class,phylum` | comma-separated ranks, innermost first |

The input taxid must have rank `species` — non-species inputs error out.

## Visualisation semantics

For each ring (taxon at a given rank):

- **Circle radius** is a function of `named_species` in the clade. With `--scale log` (default), radii are computed as `log10(species)` mapped to a pixel range; with `--scale linear` they are proportional. A horizontal axis at the bottom shows the radius ↔ species-count mapping.
- **Light-blue wedge** sweeps clockwise from 12 o'clock, with arc fraction = `species_with_assembly / named_species`.
- **Dark-blue sub-arc** drawn on top of the wedge, with arc fraction = `species_with_annotation / named_species`. Because every annotated species has an assembly, this sub-arc is always a subset of the assembly wedge.
- **Thin grey stroke** for the remaining circumference: species in the clade without any assembly.

## Development

```bash
pytest                      # unit tests
taxonview 9606 -o /tmp/x.html   # smoke test
```

The codebase:

- `src/taxonview/taxonomy.py` — ete3 wrappers: `resolve_lineage`, `descendant_species`.
- `src/taxonview/aggregate.py` — chunked SQLite queries against `taxid_features`.
- `src/taxonview/render.py` + `templates/taxonview.html.j2` — Jinja2 + vendored D3 v7.
- `src/taxonview/cli.py` — argparse entry point.

### Cross-checking against euka_survey

You can verify TaxonView's per-clade numbers match euka_survey's `query_clade.py`:

```bash
python ../euka_survey/query_clade.py 33416 \
  --db ../euka_survey/eukaryote_taxid_features_2026_04_13.db
```

`total_organisms`, `assembly_orgs`, `annotation_orgs`, `assembly_count`, `annotation_count` should match TaxonView's `named_species`, `species_with_assembly`, `species_with_annotation`, `total_assemblies`, `total_annotations` for the same taxid.

## Not in this version

- Short-/long-read counts (the DB has them, but they aren't part of the radial design).
- Ranks above class.
- Multi-species comparison or interactive species selector (the CLI produces a single static report per run).
