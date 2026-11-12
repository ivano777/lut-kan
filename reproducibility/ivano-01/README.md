# IVANO-01 - CPU benchmark evidence

This package contains a CPU battery:
**35 configurations, one run per configuration**. Configuration definitions are in
[`configs/experiments/cpu`](../../configs/experiments/cpu).

## 1. Install the project and dependencies

Run the commands from the repository root using local Python or a virtual
environment. The installation sequence below was verified with Python 3.11:

```powershell
python -m pip install -e ".[numba]" pykan==0.2.8 torch scipy scikit-learn matplotlib
python -m pip check
```

The installation command uses the core dependencies and Numba extra from
`pyproject.toml`. PyKAN 0.2.8 does not declare its runtime dependencies, so the
command explicitly includes PyTorch, SciPy, scikit-learn and Matplotlib.
PyKAN provides `from kan import KAN`; the unrelated `kan` distribution is not
required. No dependency files need to be edited.

The installation command was checked in an empty environment and used to execute
all 35 delivered CPU configurations successfully. Only PyKAN is pinned by the
command above, so future installations may resolve different dependency versions.
Hardware, software and thread limits used for the delivered results are in
[environment/environment.json](environment/environment.json).
Further command explanations are in [commands.md](commands.md).

Reference: PyKAN 10->8, grid 8, k 3, model/input seeds 0, 1,024 inputs,
L64, linear interpolation, symmetric int8 and float16 metadata.

## 2. Execute the CPU battery once per configuration

```powershell
python -m scripts.run_plan configs/experiments/cpu --count 1 --dry-run
python -m scripts.run_plan configs/experiments/cpu --count 1 --threads 1
```

The YAMLs write to `outputs/tesi/cpu_*`. Use an empty output directory to keep
the series separate: `logging.versioning: increment` retains existing runs.
Each timed backend measurement uses the configured 10 warmup and 100 inference
iterations. `count` controls complete experiment executions, not those iterations.

To generate tables from a root containing only those CPU runs:

```powershell
python -m scripts.collect_results --root outputs/tesi --outdir outputs/tesi/summary --group_keys exp_name
```

The experiment names distinguish architectures, batch sizes and other settings.
Do not collect a root containing unrelated experiments or copied results.

## 3. Regenerate the delivered CSV tables

The delivered run files are in [results/](results/); the complete console output
for the CPU battery is in [logs/cpu-plan.txt](logs/cpu-plan.txt). Each run contains `results.json`,
`resolved_config.yaml`, `env.json` and `run_meta.json`, with their original contents.
Recorded local paths are metadata, not paths required on another machine.

```powershell
python -m scripts.collect_results --root reproducibility/ivano-01/results --outdir reproducibility/ivano-01/summary --group_keys exp_name
```

This command only reads saved results. It does not run any inference.
In [summary/](summary/), `all_runs.csv` contains 35 individual rows; each
`table_*.csv` contains 35 aggregate rows, one per configuration. Accuracy, speed
and memory are in separate tables; `table_main.csv` is a selection.
With one run, each mean equals the observed value; standard deviations and
confidence intervals are undefined. RMSE is retained in `all_runs.csv` but is
not aggregated by the collector. No graphs are required for this comparison.

## 4. Findings from this battery

The reference configuration achieved a Numba B-spline-to-LUT speedup of approximately
**13.2 times**. Higher ratios were observed in other configurations, including
**16.9 times** for L16 and **16.7 times** for a 16→8 layer. Higher observed ratios
occurred with both increases and decreases in configuration parameters; these
individual measurements do not establish a monotonic trend or a stable performance
ranking. Source for the reference measurement:
[table_speed.csv](summary/table_speed.csv#L35): `cpu_reference` (34).

| Reference backend | Time per batch (ms) |
|---|---:|
| Direct B-spline Numba | 6.585656 |
| LUT Numba | 0.500501 |

The ratio is `6.585656 / 0.500501 = 13.15813`, recorded in
`speedup_lut_numba_vs_bspline_numba__mean`. These are individual measurements;
small timing differences do not establish a stable ranking.

The following table compares approximation error and LUT storage as L increases.

- MAE: [table_accuracy.csv](summary/table_accuracy.csv), column `out_mae__mean`;
  `cpu_L16` (2), `cpu_L32` (3), `cpu_reference` (34), `cpu_L128` (1).
- LUT bytes: [table_memory.csv](summary/table_memory.csv), column `lut_bytes__mean`;
  `cpu_L16` (2), `cpu_L32` (3), `cpu_reference` (34), `cpu_L128` (1).

| L | MAE | LUT bytes reported by the runner/collector |
|---|---:|---:|
| 16 | 2.027e-5 | 22,460 |
| 32 | 1.800e-5 | 40,380 |
| 64 | 1.787e-5 | 76,220 |
| 128 | 1.773e-5 | 147,900 |

- Increasing L gives diminishing accuracy gains while storage grows substantially.
  *[table_accuracy.csv](summary/table_accuracy.csv): `out_mae__mean`, `cpu_L16` (2), `cpu_L32` (3), `cpu_reference` (34), `cpu_L128` (1);
  [table_memory.csv](summary/table_memory.csv): `lut_bytes__mean`, `cpu_L16` (2), `cpu_L32` (3), `cpu_reference` (34), `cpu_L128` (1).*
- Asymmetric quantization gives MAE 9.718e-6, about 46% lower than the symmetric
  reference, with the same reported array footprint in this configuration.
  *[table_accuracy.csv](summary/table_accuracy.csv): `out_mae__mean`, `cpu_reference` (34), `cpu_uint8_asymmetric` (35);
  [table_memory.csv](summary/table_memory.csv): `lut_bytes__mean`, `cpu_reference` (34), `cpu_uint8_asymmetric` (35).*
- Nearest interpolation gives about 3.1 times the linear reference MAE and unchanged
  reported memory. Its observed LUT time is 0.679 ms versus 0.501 ms for linear;
  no speed advantage is observed in this battery.
  *[table_accuracy.csv](summary/table_accuracy.csv): `out_mae__mean`, `cpu_L64_nearest` (4), `cpu_reference` (34);
  [table_memory.csv](summary/table_memory.csv): `lut_bytes__mean`, `cpu_L64_nearest` (4), `cpu_reference` (34);
  [table_speed.csv](summary/table_speed.csv): `ms_lut_numba__mean`, `cpu_L64_nearest` (4), `cpu_reference` (34).*
- Float32 metadata barely changes MAE (1.779e-5 versus 1.787e-5), while increasing
  reported memory from 76,220 to 80,700 bytes.
  *[table_accuracy.csv](summary/table_accuracy.csv): `out_mae__mean`, `cpu_meta_float32` (21), `cpu_reference` (34);
  [table_memory.csv](summary/table_memory.csv): `lut_bytes__mean`, `cpu_meta_float32` (21), `cpu_reference` (34).*
- Tabulating the full `phi` gives higher MAE (4.064e-4) than `spline_component`.
  *[table_accuracy.csv](summary/table_accuracy.csv): `out_mae__mean`, `cpu_phi` (33), `cpu_reference` (34).*

These are numerical approximation errors, not person-detection accuracy.

The runner/collector memory report omits reconstruction arrays: the complete reference artifact has an additional 960 bytes (77,180 bytes in total).
Neither measure represents total process RAM or firmware peak RAM.

## 5. Interpretation, diagnostics and provenance

Fixed model and input seeds identify the same numerical case. Changing grid,
degree or architecture changes the model; grid and degree may also change the
extended domain and the fraction of out-of-domain inputs. Read the OOB fields
before attributing error differences solely to conversion settings.

All 35 runs completed; none were excluded. Each run's `resolved_config.yaml`
contains its effective settings and numerical seeds; `run_meta.json` records
the start time and Git HEAD at execution time. The recorded hash does not capture
uncommitted changes. The single console log
[logs/cpu-plan.txt](logs/cpu-plan.txt) contains the output of all 35 runs.

The collector supports grouping by `exp_name`; this affects CSV grouping,
not model inference or the raw measurements.

The saved results contain finite numerical metrics and no backend errors. Maximum
absolute differences across the 35 runs are 3.58e-7 for B-spline versus PyKAN and
2.38e-7 for Numba LUT versus reference LUT; NumPy LUT matches reference LUT exactly.
These are observations from the runner's existing comparison metrics in
`results.json`, not a separate validation tool.

With batch size 1, PyKAN emitted warnings about auxiliary standard-deviation
estimates requiring more than one sample. The warnings are retained in the console
log; all runs completed with process exit code 0 and finite benchmark output metrics.
Timing on other machines need not match these measurements.

Additional parameter notes and observations are in the
[CPU README](../../configs/experiments/README.md). The
[model-seed experiment](../../configs/experiments/model_seed_mae/README.md)
is a separate experiment and is not included in this 35-run battery.
