# CPU experiments

YAML overrides in `cpu/` extend `configs/ncaa_revision_base.yaml`.
From the repository root, with the Python environment active:

```powershell
# Validate without running.
python -m scripts.run_plan configs/experiments/cpu --dry-run

# Repeat one configuration.
python -m scripts.run_series configs/experiments/cpu/cpu_reference.yaml

# Run all YAMLs in one or more files/directories.
python -m scripts.run_plan configs/experiments/cpu --count 10 --threads 1
```

Defaults: `--count 10`, `--threads 1`. Both commands use the original runner.
Results follow `logging.out_dir`; use `logging.versioning: increment`.

Collect statistics for one configuration:

```powershell
python -m scripts.collect_results --root outputs/tesi/cpu_L32 --outdir outputs/tesi/cpu_L32/summary
```

Select the intended runs: `outputs/tesi` also contains historical copies.
