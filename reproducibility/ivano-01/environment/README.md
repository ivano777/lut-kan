# IVANO-01 execution environment

[environment.json](environment.json) records the CPU, Windows build, Python,
thread limits and installed package versions for the delivered CPU battery.
Package versions were read from the interpreter used
to launch the battery. This is an inventory, not a verified installation lockfile.

## Read the environment information

Run these commands from the repository root, using the same Python interpreter
as the benchmarks. They report the current environment; they do not recreate it
or automatically generate the layout of `environment.json`.

| JSON field | Command |
|---|---|
| `cpu` (Windows PowerShell) | `Get-CimInstance Win32_Processor \| Select-Object -ExpandProperty Name` |
| `os.name`, `os.build` | `python -c "import platform; print(platform.system()); print(platform.version())"` |
| `python.version` | `python --version` |
| `python.implementation`, `python.architecture`, `python.bits` | `python -c "import platform, struct; print(platform.python_implementation()); print(platform.machine()); print(struct.calcsize('P') * 8)"` |
| `packages` | `python -m pip list --format=json` |

For a text listing of installed dependencies, use `python -m pip freeze`.

`device` is an experiment setting, not a detected hardware capability. To inspect
the effective reference configuration:

```powershell
Get-Content reproducibility/ivano-01/results/cpu_riferimento/run_000/resolved_config.yaml | Select-String 'device:'
```

`thread_limits` comes from `--threads 1` in the documented execution command.
`run_series` sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`
and `NUMBA_NUM_THREADS` to that value in each child process. To inspect values
already set in the current PowerShell session:

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -in 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS' }
```

This may print nothing: limits set only in benchmark child processes do not
change the parent terminal's environment. The runner also records the effective
Numba thread count in `results.json`, under `numba.num_threads`.
