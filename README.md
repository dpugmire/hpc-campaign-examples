# HPC Campaign Examples

This repository contains end-to-end examples for
[HPC Campaign](https://github.com/ornladios/hpc-campaign). The first example is
a 2D uniform-grid ideal-MHD Orszag-Tang vortex simulation with ADIOS2 output,
ensemble execution, derived analysis, statistics, campaign ingestion, schema
validation, and visualization.

The `main` branch uses only APIs available on the current `hpc-campaign`
`master` branch. This `provenance-pr-102` branch demonstrates the W3C PROV API
proposed by
[hpc-campaign PR #102](https://github.com/dpugmire/hpc-campaign/pull/102).
See [PROVENANCE.md](PROVENANCE.md) for the complete data-to-PROV mapping.

## Requirements

- Python 3.10 or newer
- CMake 3.18 or newer
- A C++17 compiler
- ADIOS2 with C++ bindings
- MPI, unless the solver is configured with `OT_ENABLE_MPI=OFF`

On this branch, the Python project installs the matching experimental
`hpc-campaign` branch along with the Matplotlib dependency used by the
rendering script:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

For development against an existing checkout instead, install that checkout
after installing this project so its editable package takes precedence:

```bash
python -m pip install -e /path/to/hpc-campaign
```

## Build the solver

MPI build:

```bash
cmake -S . -B build -DOT_ENABLE_MPI=ON
cmake --build build -j
```

Serial build:

```bash
cmake -S . -B build -DOT_ENABLE_MPI=OFF
cmake --build build -j
```

## Run an ensemble

The JSON files in `ensembles/` describe named runs and their solver settings.
Run the small ensemble with:

```bash
python scripts/run_ensembles.py \
  --binary ./build/ot_mhd \
  --config ensembles/simple.json
```

The resolution sweep is run similarly:

```bash
python scripts/run_ensembles.py \
  --binary ./build/ot_mhd \
  --config ensembles/resolution_sweep.json
```

Use `--dry-run` to inspect commands without launching simulations. Each run
directory contains `output.bp` and `input_parameters.txt`.

The primary ADIOS dataset contains fields including:

- `rho` and `pressure`
- `vx`, `vy`, and `vz`
- `bx`, `by`, and `bz`
- `speed` and `current_z`
- scalar diagnostics such as `time`, energy totals, and divergence measures

Optional command-line arguments can also write `psi`, momentum components, and
total energy density. A run can prepend a code-specific string to every ADIOS
variable name; the data remains self-describing.

## Create a campaign

Register the primary output from every run:

```bash
python scripts/add_adios_files_to_campaign.py \
  ./runs \
  --archive mhd.aca \
  --recreate \
  --showInfo
```

The ingest script embeds `schemas/mhd_orszag_tang.yaml` and immediately calls
`Manager.validate_schema()`. The schema describes an append-mode `output.bp`
inside each run directory. It intentionally does not hard-code a time-variable
name because the solver can prefix physical ADIOS names. ADIOS remains the
authoritative description of variables inside the file.

Schema validation is metadata-only. Additional analysis, statistics, images,
and text datasets are allowed in each run. After validating the layout, the
script authors the campaign's W3C PROV document: simulation runs, logical
variables, software agents, Plans, and exact generation/derivation relations.

To write a reviewable PROV-JSON copy beside the campaign, add:

```bash
--exportProv ./mhd.prov.json
```

## Add derived fields and statistics

Create `analysis.bp` containing `grad_rho_abs`, `grad_pressure_abs`, and
`div_b`, then register it with the source datasets:

```bash
python scripts/add_adios_files_to_campaign.py \
  ./runs \
  --archive mhd.aca \
  --withDerived \
  --recreate
```

Add per-step min, max, mean, median, standard deviation, and variance datasets:

```bash
python scripts/add_adios_files_to_campaign.py \
  ./runs \
  --archive mhd.aca \
  --withDerived \
  --withStats \
  --recreate \
  --showInfo
```

Existing derived and statistics datasets are reused. Use `--forceDerived` or
`--forceStats` to regenerate them.

## Render visualizations

Render pressure from every primary dataset and store the images in the
campaign:

```bash
python scripts/render_adios_visualizations_to_campaign.py \
  --archive mhd.aca \
  --datasetPattern '*/output.bp' \
  --variable pressure \
  --data_root ./runs \
  --allSteps
```

Render velocity and magnetic streamlines:

```bash
python scripts/render_adios_visualizations_to_campaign.py \
  --archive mhd.aca \
  --datasetPattern '*/output.bp' \
  --allVariables \
  --visType streamlines \
  --data_root ./runs \
  --replace
```

The rendering script uses `Manager.visualization()` to register explicit image
items, source variables, semantic roles, a thumbnail, and rendering metadata.
It also records one Visualization Activity per sequence. The output logical
variable points to an embedded sequence manifest, and qualified PROV
derivations identify every field used for geometry, color, or contours.

## Run the tests

```bash
python -m pytest -q
python -m ruff check .
```

The tests validate the schema against a two-run campaign and exercise the
scientific-name resolution, multiple-input derived calculation, statistics,
simulation generation, exact derivation parents, and visualization provenance.
Generated campaigns and simulation products are ignored by Git.
