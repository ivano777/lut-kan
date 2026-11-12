# IVANO-01 — experiment commands

Run these PowerShell commands from the repository root using either a virtual
environment or your local Python installation, with the project dependencies
installed. Follow the [installation sequence](README.md#1-install-the-project-and-dependencies)
to install the project using the existing TOML core/Numba dependencies and explicit PyKAN runtime dependencies.
The recorded versions are listed in [environment/environment.json](environment/environment.json).
This document uses the current scripts. The delivered results are documented in the [IVANO-01 report](README.md).

## 1. CPU configuration comparisons

Validate the configurations without executing experiments or drawing random seeds:

```powershell
python -m scripts.run_plan configs/experiments/cpu --count 1 --dry-run
```

Run only the L64 reference, or run every CPU configuration once:

```powershell
# One configuration.
python -m scripts.run_series configs/experiments/cpu/cpu_reference.yaml --count 1 --threads 1

# Alternatively, the complete CPU plan (includes the reference).
python -m scripts.run_plan configs/experiments/cpu --count 1 --threads 1
```

These are alternatives: executing both adds two reference runs. Each run prepares
the model and LUT and writes its own results. Timing uses the configured warmup
and measurement iterations (10 and 100 in the base configuration).
Use `--count 10` only when repeated execution is intended; it is not needed to
aggregate existing results. The delivered CPU battery uses `--count 1`.

`logging.out_dir` in each YAML controls the output directory. With
`logging.versioning: increment`, rerunning adds runs rather than replacing them.
Use a new output directory for a separate series. See the
[CPU README](../../configs/experiments/README.md) for parameters and observations.

## 2. Collect CSV tables without rerunning experiments

For one configuration, for example L32:

```powershell
python -m scripts.collect_results --root outputs/tesi/cpu_L32 --outdir outputs/tesi/cpu_L32/summary
```

Use the directories of the series you want to analyze. The collector includes all
`results.json` files below each root, including older runs or copies if present.
If saved results are stored elsewhere, replace the collection paths accordingly;
the input root must contain the selected per-run `results.json` files.

Each `summary/` contains:

- `all_runs.csv`: one row per run.
- `table_accuracy.csv`, `table_speed.csv`, `table_memory.csv`: aggregate metrics.
- `table_main.csv`: a selection of aggregate metrics.

For a directory containing one configuration group, each aggregate table has one
row. With one run, the mean equals the recorded value and standard deviation and
confidence intervals are undefined. To collect a complete battery with one row
per configuration, use distinct experiment names and `--group_keys exp_name`:

```powershell
python -m scripts.collect_results --root reproducibility/ivano-01/results --outdir reproducibility/ivano-01/summary --group_keys exp_name
```

This regenerates the delivered tables without rerunning experiments.
Default grouping alone does not distinguish every architecture or batch setting.

## 3. MAE sensitivity to model initialization

This separate experiment uses PyKAN 10→8, L32 and 1,024 inputs. The input seed is
fixed at 0; each run draws a model seed and records it in `resolved_config.yaml`.

```powershell
python -m scripts.run_plan configs/experiments/model_seed_mae --dry-run
python -m scripts.run_plan configs/experiments/model_seed_mae --count 10 --threads 1
```

Then collect and plot the results (skip execution above when results already exist):

```powershell
python -m scripts.collect_results --root outputs/tesi/model_seed_mae_10x8_10 --outdir outputs/tesi/model_seed_mae_10x8_10/summary
python -m scripts.plot_seed_mae outputs/tesi/model_seed_mae_10x8_10
```

For previously saved results, use their experiment directory in both commands.
The plot script reads only `summary/all_runs.csv` and produces
`mae.png`, `mae.pdf` and `mae_statistics.json`. It is dedicated to this experiment.
Interpretation and results: [model-seed README](../../configs/experiments/model_seed_mae/README.md).

Running a YAML containing `seed: random` produces new seeds, not the original
models. Exact-case replay requires the saved `resolved_config.yaml` with numerical
seeds, using the appropriate source version and dependencies.
