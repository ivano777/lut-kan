"""Repeat one experiment configuration using the original runner."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.utils.parse_config import load_and_validate


def add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--count', type=int, default=10, help='Runs per configuration (default: 10)')
    parser.add_argument('--threads', type=int, default=1, help='Threads per process (default: 1)')
    parser.add_argument('--dry-run', action='store_true', help='Validate and print without running')


def validate_config(config: Path) -> Path:
    config = Path(config).resolve()
    cfg, _ = load_and_validate(config)
    if cfg.logging.versioning != 'increment':
        raise ValueError(f'{config}: repeated runs require logging.versioning: increment')
    if getattr(cfg.evaluation_inputs, 'fixture', None):
        raise ValueError(f'{config}: custom input fixtures are not supported by the standard runner')
    return config


def run_series(config: Path, count: int = 10, threads: int = 1, dry_run: bool = False) -> None:
    if count < 1 or threads < 1:
        raise ValueError('count and threads must be positive')
    config = validate_config(config)
    print(f'{config}: {count} runs, {threads} thread(s)', flush=True)
    if dry_run:
        return
    env = os.environ.copy()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS'):
        env[key] = str(threads)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    for index in range(count):
        print(f'[{index + 1}/{count}] {config.name}', flush=True)
        subprocess.run([sys.executable, '-m', 'scripts.run_experiment', str(config)],
                       cwd=REPO_ROOT, env=env, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    add_run_options(parser)
    args = parser.parse_args()
    try:
        run_series(**vars(args))
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
