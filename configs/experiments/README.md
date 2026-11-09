# CPU experiments

YAML overrides in `cpu/` extend `configs/ncaa_revision_base.yaml`.
From the repository root, with the Python environment active:

```powershell
# Validate without running.
python -m scripts.run_plan configs/experiments/cpu --count 1 --dry-run

# Run one configuration once.
python -m scripts.run_series configs/experiments/cpu/cpu_reference.yaml --count 1

# Run all YAMLs in one or more files/directories.
python -m scripts.run_plan configs/experiments/cpu --count 1 --threads 1
```

Defaults: `--count 1`, `--threads 1`. Both commands use the original runner.
Results follow `logging.out_dir`; use `logging.versioning: increment`.
With fixed seeds, one run is enough for an initial comparison of precision and array
memory. Each enabled timing measurement already averages 100 inference calls in the
base configuration. Repeated complete runs assess timing variability, not new models
or inputs unless the seeds change.

`runtime.seed` and `float_model.arch.seed` accept an integer or `random`.
The runner resolves each `random` independently once per run and saves the integer
in `resolved_config.yaml`. With PyKAN these control inputs and model weights,
respectively; Jacobi and dummy use `runtime.seed` for both. Validation/dry-run
does not draw seeds. The source YAML is unchanged.

Collect statistics for one configuration:

```powershell
python -m scripts.collect_results --root outputs/tesi/cpu_L32 --outdir outputs/tesi/cpu_L32/summary
```

Run the collector separately for each configuration's output directory. Its
`table_accuracy.csv`, `table_speed.csv`, `table_memory.csv` and `table_main.csv`
contain one aggregate row per configuration when that directory contains only one
parameter group. `all_runs.csv` instead contains one row per individual run.
With one run, the mean is that run's value; standard deviation and confidence
intervals are undefined. Reusing an output directory includes previous runs too.
For now, use these CSV tables for comparisons; no additional plotting step is required.

## Observations from the previous CPU experiments

These results come from the historical ten-run series on an Intel Core i7-1255U
with Python 3.11.15. The reference uses PyKAN 10→8, grid 8, k 3, seeds 0,
1,024 inputs, L64, linear interpolation and symmetric int8 quantization.
Fixed-seed repetitions repeat the same numerical case; they are not independent
samples of approximation error. The figures below do not imply classification accuracy.

| Samples per segment | MAE | Complete LUT artifact array bytes |
|---|---:|---:|
| L16 | 2.027e-5 | 23,420 |
| L32 | 1.800e-5 | 41,340 |
| L64 | 1.787e-5 | 77,180 |
| L128 | 1.773e-5 | 148,860 |

- Increasing L improves error with diminishing returns while memory grows substantially.
- Asymmetric quantization gives MAE 9.718e-6, about 46% lower than the symmetric
  reference, with the same artifact array footprint in this experiment.
- Nearest interpolation gives MAE 5.596e-5 (about 3.1 times the linear reference),
  unchanged memory, and no observed speed advantage. Its timings came from a separate session.
- Tabulating the full `phi` function gives MAE 4.064e-4, substantially higher than
  `spline_component`; lower execution time alone does not make it preferable.
- Float32 metadata barely changes MAE (1.779e-5 versus 1.787e-5), while increasing
  the complete array footprint from 77,180 to 81,660 bytes.
- The reference LUT Numba evaluation takes about 0.436 ms per batch, roughly 15 times
  faster than direct B-spline Numba evaluation. Small timing differences need repeated verification.

The memory figures above include all artifact arrays, calculated with the existing
`artifact_memory_bytes` helper. The collector uses the runner's partial memory report,
which omits reconstruction arrays for `spline_component` (960 bytes for this 10→8 case).
Neither measure represents total process RAM.

TODO: Separate one-time preparation (configuration loading, seed resolution for the model, model initialization, edge extraction, LUT construction, backend packing, Numba initialization, memory calculation, and shared artifact saving) from repeated execution on batches with recorded input seeds.
Keep result production separate: save per-batch errors and timings, then use the collector to aggregate the evaluations.
