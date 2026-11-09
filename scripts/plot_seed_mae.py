"""Plot the PyKAN 10→8 experiment: random weights, fixed inputs, L32 LUT."""
from pathlib import Path
import argparse
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('root', type=Path, help='Experiment output directory containing summary/all_runs.csv')
args = parser.parse_args()
root = args.root
summary = root / 'summary'
df = pd.read_csv(summary / 'all_runs.csv')
count = len(df)
v = df.out_mae.to_numpy(dtype=float)
stats = {
    'runs': len(v), 'mean': float(v.mean()), 'median': float(np.median(v)),
    'std': float(v.std(ddof=1)), 'min': float(v.min()), 'max': float(v.max()),
    'p05': float(np.percentile(v, 5)), 'p95': float(np.percentile(v, 95)),
    'p99': float(np.percentile(v, 99)),
    'coefficient_of_variation_percent': float(v.std(ddof=1) / v.mean() * 100),
}
(summary / 'mae_statistics.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(2, 2, figsize=(15, 10), layout='constrained')
scale = 1e6
w = v * scale
ax = axes[0, 0]
ax.plot(np.arange(1, count + 1), w, '.-', color='#2764a5', lw=.8, ms=4)
ax.axhspan(stats['p05']*scale, stats['p95']*scale, color='#2764a5', alpha=.10, label='MAE P5–P95 range')
ax.axhline(stats['mean']*scale, color='#d15b28', label='Mean')
ax.axhline(stats['median']*scale, color='#27865c', ls='--', label='Median')
ax.set(title='MAE per run — each point is a different model', xlabel='Run (execution order)', ylabel='MAE × 10⁻⁶')
ax.legend(fontsize=9)
ax = axes[0, 1]
ax.hist(w, bins=min(14, max(4, int(np.sqrt(count)))), color='#2764a5', edgecolor='white')
ax.axvline(w.mean(), color='#d15b28', label='Mean')
ax.axvline(np.median(w), color='#27865c', ls='--', label='Median')
ax.set(title=f'Distribution of {count} MAEs', xlabel='MAE × 10⁻⁶', ylabel='Number of runs')
ax.legend()
ax = axes[1, 0]
ax.plot(np.arange(1, count + 1), np.cumsum(w)/np.arange(1, count + 1), color='#2764a5')
ax.axhline(w.mean(), color='#d15b28', ls='--', label=f'Final mean ({count} runs)')
ax.set(title='Cumulative mean', xlabel='Number of runs included', ylabel='Cumulative mean MAE × 10⁻⁶')
ax.legend()
ax = axes[1, 1]
ax.axis('off')
rows = [('Mean', stats['mean']*scale), ('Median', stats['median']*scale),
        ('Standard deviation', stats['std']*scale), ('Minimum', stats['min']*scale),
        ('5th percentile', stats['p05']*scale), ('95th percentile', stats['p95']*scale),
        ('99th percentile', stats['p99']*scale), ('Maximum', stats['max']*scale)]
table = ax.table(cellText=[[k, f'{val:.3f}'] for k,val in rows],
                 colLabels=['Statistic across run MAEs', 'Value × 10⁻⁶'], loc='center', cellLoc='left')
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 1.9)
ax.set_title(f'Relative variability (std/mean): {stats["coefficient_of_variation_percent"]:.2f}%')
fig.suptitle('MAE across model seeds — fixed inputs (seed 0)\nPyKAN 10→8 · L32 LUT, symmetric int8 · 1,024 inputs/batch', fontsize=16)
for ax in axes.flat[:3]:
    ax.grid(alpha=.2)
fig.savefig(summary / 'mae.png', dpi=170)
fig.savefig(summary / 'mae.pdf')
print(json.dumps(stats, indent=2))
