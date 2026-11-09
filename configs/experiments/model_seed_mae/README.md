# MAE across model seeds

Ten PyKAN 10→8 models with random weight initialization seeds, evaluated on the same
batch of 1,024 inputs (seed 0). L32 LUT with symmetric int8 quantization; grid 8, k 3.
This experiment measures how approximation error varies with the initial weights.

From the repository root, with the Python environment activated:

```powershell
# 1. Validate without running.
python -m scripts.run_plan configs/experiments/model_seed_mae --dry-run

# 2. Execute ten runs.
python -m scripts.run_plan configs/experiments/model_seed_mae --count 10

# 3. Collect run results and compute statistics.
python -m scripts.collect_results --root outputs/tesi/model_seed_mae_10x8_10 --outdir outputs/tesi/model_seed_mae_10x8_10/summary

# 4. Generate PNG/PDF plots and MAE statistics in JSON.
python -m scripts.plot_seed_mae outputs/tesi/model_seed_mae_10x8_10
```

Repeating step 2 adds more runs; for a separate series, change `logging.out_dir`
and use that path in steps 3 and 4. Actual seeds are saved in each run's `resolved_config.yaml`.

First series results: mean MAE **1.803×10⁻⁵**, standard deviation
**3.291×10⁻⁷** (**1.83%** of the mean), minimum **1.740×10⁻⁵**, maximum **1.852×10⁻⁵**.
MAE varies little across these ten models; this experiment does not evaluate trained networks.
The observed 1.83% relative standard deviation suggests limited sensitivity to the
model seed in this configuration, so further investigation is not a priority for now.
This variability still matters when comparing small improvements (around 1–2%);
such comparisons should use the same model and input seeds across configurations.
These findings do not establish seed insensitivity for other configurations or trained networks.
The plots show MAE per run, its distribution, the cumulative mean, and summary statistics.
Percentiles describe the MAEs across runs and are only indicative with ten samples.
The plotting script is specific to this configuration and reads only `summary/all_runs.csv`.

Outputs in `summary/`: `all_runs.csv`, the collector's aggregate tables,
`mae.png`, `mae.pdf`, `mae_statistics.json`.
