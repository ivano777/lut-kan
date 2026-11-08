"""Run a series for every YAML found in one or more files/directories."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_series import add_run_options, run_series, validate_config


def find_configs(paths: list[Path]) -> list[Path]:
    configs = set()
    for path in paths:
        path = Path(path).resolve()
        if not path.exists():
            raise ValueError(f'Path does not exist: {path}')
        candidates = path.rglob('*') if path.is_dir() else [path]
        found = {p.resolve() for p in candidates if p.is_file() and p.suffix.lower() in ('.yaml', '.yml')}
        if not found:
            raise ValueError(f'No YAML configurations found in: {path}')
        configs.update(found)
    return sorted(configs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path, help='YAML files or directories (recursive)')
    add_run_options(parser)
    args = parser.parse_args()
    try:
        if args.count < 1 or args.threads < 1:
            raise ValueError('count and threads must be positive')
        configs = [validate_config(p) for p in find_configs(args.paths)]
        print(f'{len(configs)} configurations, {len(configs) * args.count} runs', flush=True)
        for config in configs:
            run_series(config, args.count, args.threads, args.dry_run)
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
