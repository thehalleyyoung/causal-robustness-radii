# Reproducing the results

All numbers in `paper/tool_paper.tex` and `README.md` are produced by the commands
below; their raw outputs are committed under `results/`.

## Environment

```bash
uv venv -p 3.12 .venv
uv pip install -p .venv/bin/python networkx numpy scipy scikit-learn click jinja2 pandas pyarrow mip \
    pytest pytest-xdist xlrd openpyxl statsmodels
```

R comparators (dagitty, sensemakr, EValue, bnlearn) run in a container on Modal
(`experiments/modal_r.py`, image `rocker/r-ver:4.4.2`, CRAN packages installed at build
time; package versions are recorded in `results/*/r_sessionInfo*.txt`). The same R scripts
run locally with `Rscript experiments/r/<script>.R <in_dir> <out_dir> [n_boot]` if R and the
four packages are installed.

## Tests

```bash
cd implementation && ../.venv/bin/python -m pytest tests -q -n 2      # full suite -> results/test_suite.log
cd implementation && ../.venv/bin/python -m pytest tests/test_radius_exact.py -q   # radius cross-checks
```

## RQ1: built-in DAG library sweep

```bash
.venv/bin/python experiments/published_sweep.py --samples 500 --seed 42 --max-nodes 12 --max-k 3
# -> results/published_sweep.json
```

## RQ2: synthetic misspecification benchmark

Regime B (weak effects, null queries; main benchmark):

```bash
.venv/bin/python experiments/synthetic_benchmark.py pilot --wlow 0.3 --p-null 0.3 --effect-scale 0.15   # generator calibration -> results/synthetic_pilot.jsonl
.venv/bin/python experiments/synthetic_benchmark.py generate --n 400 --seed 2026            # defaults: --generator v2 --wlow 0.3 --p-null 0.3 --effect-scale 0.15
.venv/bin/python experiments/synthetic_benchmark.py radii --max-k 3
modal run experiments/modal_r.py --script synthetic_comparators.R --indir results/synthetic/scenarios --outdir results/synthetic --extra 100
.venv/bin/python experiments/synthetic_benchmark.py bootstrap
.venv/bin/python experiments/synthetic_benchmark.py evaluate
# -> results/synthetic/{radii.jsonl,r_comparators.csv,bootstrap_stability.csv,per_scenario.csv,summary.json}
```

Regime A (strong effects):

```bash
.venv/bin/python experiments/synthetic_benchmark.py generate --n 400 --seed 2026 --generator v1 --out-dir results/synthetic_strong
.venv/bin/python experiments/synthetic_benchmark.py radii --max-k 3 --out-dir results/synthetic_strong
modal run experiments/modal_r.py --script synthetic_comparators.R --indir results/synthetic_strong/scenarios --outdir results/synthetic_strong --extra 100
.venv/bin/python experiments/synthetic_benchmark.py bootstrap --out-dir results/synthetic_strong
.venv/bin/python experiments/synthetic_benchmark.py evaluate --out-dir results/synthetic_strong
```

Scenario CSVs are not committed (35 MB per regime); `generate` recreates them
byte-for-byte from the seed (checked: `cmp` on regenerated files).

## RQ3: real-data case studies

```bash
.venv/bin/python experiments/real_data.py --dataset sachs --max-k 3
.venv/bin/python experiments/real_data.py --dataset adult --max-k 3
modal run experiments/modal_r.py --script real_comparators.R --indir results/real --outdir results/real --extra 200
.venv/bin/python experiments/real_summary.py
# -> results/real/{sachs,adult}_{radii.json,localtests.csv,sensitivity.csv,bootstrength.csv,bootamats.json}, results/real/summary.json
```

## Tables and figures in the paper

```bash
.venv/bin/python experiments/make_tables.py     # -> paper/tables/*.tex
cd paper && pdflatex tool_paper && bibtex tool_paper && pdflatex tool_paper && pdflatex tool_paper
```

## Bibliography check

```bash
.venv/bin/python paper/verify_refs.py           # -> paper/refs_verification.json (Crossref, DataCite, arXiv)
```

## Cost logs

`results/modal_costs.jsonl` (Modal runs). No paid LLM APIs were used, so there is no
`results/api_costs.jsonl`.

## Estimator audit (local CPU; no paid calls)

Run the focused controls with `PYTHONPATH=implementation python -m pytest implementation/tests/test_ols_identifiability.py implementation/tests/test_radius_exact.py -q`. The preserved full run has 1,394 passes and 2 skips. The later focused run includes the missing-baseline guard. `audit/journal/estimator_stress.py` regenerates the rank-deficient control; its baseline implementation bytes are preserved in `audit/journal/originals/estimate.py`.

`audit/journal/check_estimator_agreement.py` compares old and current classifiers on all adjustment subsets of the archived synthetic and real inputs. Its explicit source-root argument must point to a checkout with regenerated scenario CSVs and real data; input hashes are recorded in `estimator-agreement.json`. This is reanalysis of existing data. It found no classification changes in 51,872 finite designs; it does not remeasure runtime or replicate the R comparators. New round spending is $0, with no provider billing reconciliation implied.

## October 2026 numerical checkpoint

Build the current root publication PDF with `python3 scripts/build_paper.py` (requires pdflatex and BibTeX). Intermediate publication PDFs are created in a temporary directory. The previous publication PDF was externally hash-archived.

With the implementation importable and NumPy/SciPy/statsmodels installed, run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=implementation python audit/wave2/location_probe.py /tmp/location-replay.json` and `PYTHONPATH=implementation python audit/wave2/independent_controls.py`. The latter refreshes its raw JSON; deterministic scientific outputs should agree, runtime fields can vary. Frozen before/after results and the initial milder passing arm are retained. This is a synthetic numerical intervention, not a new real-data replication or a RoCA baseline.

Stage the local site with `python3 scripts/build_site.py`; serve `_site` with any static HTTP server. All local HTML links are checked. GitHub Pages workflow is manual-only and has not run. Configure GitHub Pages to use Actions before choosing to deploy; no deployment or DOI is implied by these files.
