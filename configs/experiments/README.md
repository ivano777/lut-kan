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

## Parameters

The reference configuration uses PyKAN 10->8, grid 8, degree 3, 1,024 inputs,
L64, linear interpolation, symmetric int8 quantization and float16 metadata.
All YAMLs in `cpu/` inherit from [`configs/ncaa_revision_base.yaml`](../ncaa_revision_base.yaml),
which in turn inherits from [`configs/spec.yaml`](../spec.yaml), using `_base_`.
Settings are merged in this order: `spec.yaml`, `ncaa_revision_base.yaml`, then
the individual experiment YAML; later values override earlier ones.
The runner saves the resulting effective configuration in `resolved_config.yaml`.

| Configuration field | Meaning and effect |
|---|---|
| `float_model.arch.width` | Specifies the input and output dimensions of the single KAN layer. With `[10, 8]`, each input vector contains 10 values and the layer produces 8 output values. The layer has 10 × 8 = 80 edges. Increasing either dimension increases the number of edges, computational work and LUT storage required. |
| `float_model.arch.grid` | Defines the number of intervals in the initial spline input range (`[-1, 1]` in the reference) and contributes to the number of knots. |
| `float_model.arch.k` | Defines the spline degree and also contributes to the total number of knots. |
| `evaluation_inputs.num_samples` | Number of synthetic input vectors evaluated in the batch. Inputs are pseudo-randomly generated using `runtime.seed`; a fixed seed reproduces the same batch when the input generation settings are unchanged. |
| `evaluation_inputs.inputs.clip_min`, `clip_max` | Define the allowed range of generated input values before passing them to both PyKAN and the LUT. Values below `clip_min` are replaced with `clip_min`; values above `clip_max` are replaced with `clip_max`. These limits are configured explicitly, independently of the spline domain; in the reference, `[-1.75, 1.75]` matches the extended knot range. Setting both to `null` leaves generated values unchanged, allowing OOB evaluation. |
| `converter.build_lut.L` | Samples stored per spline segment, including both endpoints; increasing L increases table storage and can reduce interpolation error. |
| `converter.value_representation` | Defines what is stored in the LUT and how its values are used during inference to reconstruct the complete edge function.<br>**`spline_component`**: stores only the spline component. During inference, the LUT value is combined with the separately computed base function and the model coefficients.<br>**`phi`**: stores samples of the complete edge function, including the base contribution and model coefficients. During inference, the reconstructed LUT value directly provides the edge contribution. |
| `converter.interp.mode` | For an input between sampled LUT positions, approximates the function value using `linear` (a weighted combination of the two adjacent samples) or `nearest` (the value of the closest sample). Each spline segment contains `L` sampled positions, including its endpoints. Interpolation reconstructs values between these LUT samples. |
| `converter.quant.dtype` | Integer storage type for LUT samples: `int8` (signed, -128 to 127) or `uint8` (unsigned, 0 to 255). Both use one byte per sample. The symmetric reference uses int8 codes from -127 to 127; the asymmetric case uses uint8 codes from 0 to 255. |
| `converter.quant.scheme` | Maps sampled function values to integer codes: `symmetric` uses a value range centered on zero; `asymmetric` uses the selected range with a stored offset. With `converter.y_range.method: minmax`, the selected bounds are the minimum and maximum sampled values. Both introduce rounding error. In this project, `uint8` requires `asymmetric`. See the range explanation in [Out-of-domain inputs](#out-of-domain-inputs). |
| `converter.quant.qmin`, `qmax` | Minimum and maximum integer codes used for quantization. The allowed limits are determined by the 8-bit data type: `[-128, 127]` for `int8` and `[0, 255]` for `uint8`. The symmetric reference uses `[-127, 127]` to keep the range symmetric around zero. |
| `converter.quant.zero_point` | An integer zero point identifies the integer code representing the real value zero. Here `symmetric` requires `0`, so code 0 represents real zero. `asymmetric` requires `auto`: this implementation instead reconstructs values as `y = y_min + scale * q`, using the stored `y_min` offset without an explicit integer zero point. |
| `converter.quant.meta_dtype` | Storage type for quantization scales and offsets (`scale` and `y_min`): `float16` (2 bytes per value) or `float32` (4 bytes per value). Affects their storage size and reconstruction error. The storage savings refer to the artifact arrays. |

Changing conversion settings on the same model differs from changing its grid,
degree or dimensions. Keep this distinction when interpreting comparisons.
Seed overrides are explained in [Seeds](#seeds); OOB policy and endpoint overrides
are explained in [Out-of-domain inputs](#out-of-domain-inputs).

## Seeds

`runtime.seed` and `float_model.arch.seed` accept an integer or `random`.
With PyKAN, `runtime.seed` controls synthetic inputs and `float_model.arch.seed`
controls model initialization. Both are 0 in the reference configuration.
Jacobi and dummy use `runtime.seed` for both model initialization and inputs.
The runner resolves each `random` independently once per run and saves the integer
in `resolved_config.yaml`; validation/dry-run does not draw seeds and the source
YAML is unchanged. `evaluation_inputs.seed` does not control input generation in
the current runner; use `runtime.seed` for that purpose.

## Repetitions

`--count 1` performs one complete experiment per configuration: model preparation,
LUT construction, evaluation and result saving. Separately, the base configuration
uses `evaluation.extra.speed.warmup_iters: 10` and `measure_iters: 100`.
Each reported latency measurement uses 10 warmup calls followed by 100 timed calls
on the same prepared batch. The reported latency is the total measured time
divided by 100. Additional calls are performed for initialization and numerical
comparisons.
These are timing repetitions, not 100 independent models, input batches or MAE
measurements. Errors are computed from backend output comparisons separately.
With fixed seeds, one complete run is enough for an initial comparison of precision
and array memory. Repeated complete runs assess timing variability, not new models
or inputs unless the seeds change.

## Out-of-domain inputs

The LUT domain is defined by the spline knots, not by L. To calculate the extended
knot domain, define:

- `grid_lower`: lower endpoint of the initial grid range.
- `grid_upper`: upper endpoint of the initial grid range.
- `grid`: number of intervals dividing the initial range.
- `k`: spline degree.
- `h`: spacing between consecutive knots.

For a uniform initial grid, PyKAN keeps the same spacing when extending it:

```text
h = (grid_upper - grid_lower) / grid

extended_grid_lower = grid_lower - k*h
extended_grid_upper = grid_upper + k*h

Number of knots after extension = grid + 1 + 2*k

Extended knot domain = [extended_grid_lower, extended_grid_upper]
```

Our adapter does not override PyKAN's default `grid_range=[-1, 1]`.
The reference configuration uses `grid=8` and `k=3`, so:

```text
grid_lower = -1
grid_upper =  1
grid       =  8
k          =  3
```

Substituting these values:

```text
h   = (1 - (-1)) / 8 = 0.25
extended_grid_lower = -1 - 3*0.25    = -1.75
extended_grid_upper =  1 + 3*0.25    =  1.75

Extended knot domain = [-1.75, 1.75]
```

Evaluation inputs are synthetically generated and optionally limited using these
parameters:

- **`evaluation_inputs.num_samples`**: number of input vectors generated.
- **`runtime.seed`**: seed for pseudo-random generation. The same seed and generation
  settings reproduce the same inputs.
- **`evaluation_inputs.inputs.clip_min`**: after generation, replaces values below
  this limit with the limit itself.
- **`evaluation_inputs.inputs.clip_max`**: after generation, replaces values above
  this limit with the limit itself.

Setting both `clip_min` and `clip_max` to `null` disables input clipping.

**`evaluation_inputs.inputs.distribution`** selects the generation method:

- **`normal`**: generates pseudo-random values concentrated around a mean. Values
  farther from the mean become less frequent. There is no fixed lower or upper bound.
  - **`evaluation_inputs.inputs.mean`**: center of the distribution.
  - **`evaluation_inputs.inputs.std`**: spread around the mean. Smaller values produce
    a tighter concentration; larger values spread inputs over a wider range.
- **`uniform`**: generates pseudo-random values within a specified interval.
  Equal-length subintervals have equal probability of receiving a value.
  Generated points are not equally spaced.
  - **`evaluation_inputs.inputs.x_min`**: lower bound of the generation interval.
  - **`evaluation_inputs.inputs.x_max`**: upper bound of the generation interval.

The reference uses `normal`, with `mean=0`, `std=1` and clipping limits
`[-1.75, 1.75]`. With `boundary: closed`, all evaluated inputs are in-domain.
These clipping limits are not recalculated automatically when `grid` or `k` changes.
The OOB configurations disable clipping, allowing generated values outside the knot
domain to reach the LUT.

The runner uses the extended knot domain to identify OOB inputs, with endpoints
handled according to `converter.oob_policy.boundary`.

The examples below use the knot range `[-1.75, 1.75]` and inputs that have not
been clipped during generation.

- `converter.oob_policy.mode: clip_x` clips the input used for the LUT lookup to
  the nearest allowed position in the knot domain.
  Example: `x=-2.0` reads the LUT at `x=-1.75`; the LUT contribution is the
  reconstructed function value at that position.
- `converter.oob_policy.mode: zero_spline` sets the tabulated contribution directly
  to the numerical value `0.0` for an OOB input.
  Example: `x=2.0` produces a tabulated contribution of `0.0`. This is an
  output value applied after reconstruction, independent of the quantization offset.
- `converter.oob_policy.boundary` determines whether an endpoint belongs to the
  domain: `closed` includes both endpoints; `half_open` excludes the upper endpoint.
  The lower endpoint `x=-1.75` is included in both cases.
  With `clip_x`, an input at or above `1.75` uses `1.75` for lookup with `closed`,
  or the closest representable value below `1.75` with `half_open`.
  With `zero_spline`, the exact input `x=1.75` is evaluated normally with `closed`,
  but produces a tabulated contribution of `0.0` with `half_open` because it is OOB.
  Inputs strictly above `1.75`, such as `x=2.0`, are OOB in both cases.

With `spline_component`, both OOB modes affect only the LUT component; the base
function is evaluated separately at the original input and combined with that
component using the model coefficients.

With `phi`, the reconstructed LUT value already represents the complete edge
contribution and is used directly. For an OOB input:

- `zero_spline`: the complete edge contribution is `0.0`.
- `clip_x`: the complete edge contribution is the reconstructed LUT value at the
  clipped input, following the boundary rules described above.

Using `phi` does not remove OOB inputs: the input domain is still bounded by the
same extended knots and interpreted according to `boundary`.

`converter.y_range.method` determines how the range of sampled function values
is calculated. The base configuration uses `minmax`.

For each edge, the function is evaluated at `L` equally spaced positions within
each segment, including both endpoints. `converter.y_range.method` selects a
separate range from those sampled values for each edge and segment:

- **`minmax`**: uses the minimum and maximum sampled values, including all samples
  in the selected range.
- **`percentile`**: uses the percentiles specified by
  `converter.y_range.lower_percentile` and `converter.y_range.upper_percentile`.
  Selecting inner percentiles narrows the range and can provide finer quantization
  steps for values within it. The trade-off is that samples outside the resulting
  representable range are clipped to the minimum or maximum integer code,
  potentially increasing their reconstruction error.

The selected range is then mapped according to `converter.quant.scheme`:
symmetric quantization makes it symmetric around zero, while asymmetric
quantization uses its lower and upper bounds to calculate the scale and offset.

Both range-selection methods use the samples calculated during LUT construction,
not the generated evaluation inputs. With the model and LUT settings unchanged,
changing only the evaluation input seed does not change these ranges.

The two quantization schemes work as follows:

- **`symmetric`**: expands the sampled range to an interval centered on zero.
  With `A = max(abs(y_min), abs(y_max))`, the range becomes `[-A, A]`.
  The reference uses int8 codes `[-127, 127]`, with `scale = A / 127`,
  reconstructing values as `y = scale * q`. No offset is needed, but when the
  sampled range is asymmetric, some integer codes cover values outside that range.

- **`asymmetric`**: preserves the sampled range `[y_min, y_max]`. The tested
  uint8 configuration uses codes `[0, 255]`, with `scale = (y_max - y_min) / 255`,
  reconstructing values as `y = y_min + scale * q`. The offset `y_min` sets the
  starting value, while `scale` sets the distance between consecutive representable
  values. This allows unsigned codes to represent negative function values as well.

If all sampled values are zero, symmetric quantization uses `scale = 1`.
If all sampled values are equal, asymmetric quantization uses `scale = 1` and
stores that constant value as the offset. In both cases, the samples are encoded
as zero.

For example, with sampled values from `-0.1` to `0.9`:

| | Symmetric | Asymmetric |
|---|---|---|
| Represented range | `[-0.9, 0.9]` | `[-0.1, 0.9]` |
| Integer codes | `[-127, 127]` | `[0, 255]` |
| Scale | `0.9 / 127 ≈ 0.00709` | `1.0 / 255 ≈ 0.00392` |
| Offset | `0` | `-0.1` |

Symmetric quantization reconstructs values without adding an offset. Asymmetric
quantization uses the available codes more efficiently when the sampled range is
not centered on zero: in this example, its smaller step can reduce rounding error.
Both configurations use one byte per table sample. The benefit depends on the
sampled range and does not guarantee a lower overall model output error.

## Collect results

Collect statistics for one configuration:

```powershell
python -m scripts.collect_results --root outputs/tesi/cpu_L32 --outdir outputs/tesi/cpu_L32/summary
```

Alternatively, collect multiple configurations together using `--group_keys exp_name`.
The collector was extended to support `exp_name` as a grouping key for the existing
`--group_keys` option. It groups runs by `experiment.name`; use a distinct name for
each configuration to obtain one aggregate row per configuration.
We used this support to generate the IVANO-01 summary tables:

```powershell
python -m scripts.collect_results --root reproducibility/ivano-01/results --outdir reproducibility/ivano-01/summary --group_keys exp_name
```

The collector's
`table_accuracy.csv`, `table_speed.csv`, `table_memory.csv` and `table_main.csv`
contain one aggregate row per group. `all_runs.csv` instead contains one row per individual run.


`out_mae`, `in_mae` and `oob_mae` compare the reference LUT implementation against
the original floating-point model (PyKAN in these experiments). Comparisons
involving the Numba LUT backend are recorded separately in `results.json`.

In collector CSVs, `oob_any_frac` is the fraction of input vectors with at least
one out-of-domain coordinate. `out_mae` covers all vectors, `in_mae` only fully
in-domain vectors, and `oob_mae` only vectors with an out-of-domain coordinate.
Aggregate tables add suffixes such as `__mean`. The runner records zero error for
an empty subset, so read its fraction before interpreting that subset's error.
Check these fields before attributing error differences solely to quantization
or interpolation.

## Results and interpretation

The shared CPU battery contains 35 configurations, with one run per configuration.
Results, source tables and interpretation are available in the
[IVANO-01 report](../../reproducibility/ivano-01/README.md#4-findings-from-this-battery).
The delivered reference measurement is 0.500501 ms per batch for LUT Numba,
approximately 13.2 times faster than direct B-spline Numba evaluation.
These timings describe the delivered measurements, not a stable performance ranking.

TODO: Separate one-time preparation (configuration loading, seed resolution for the model, model initialization, edge extraction, LUT construction, backend packing, Numba initialization, memory calculation, and shared artifact saving) from repeated execution on batches with recorded input seeds.
Keep result production separate: save per-batch errors and timings, then use the collector to aggregate the evaluations.
