# IVANO-02 — Jacobi LUT inference on ESP32-C3

This test compares the three outputs of a single Jacobi KAN layer in Python and in C++ on a Wokwi ESP32-C3. With the corrected LUT export, **all nine outputs agree within the absolute tolerance of 1e-5**. The largest absolute difference is **0.000001724**.

## Model and control inputs

The experiment reuses the [LUT-KAN MCU case generator](../../mcu_auto/scripts/gen_cases.py) and its [C++ firmware template](../../mcu_auto/templates/pio_project/src/main.cpp). The [case configuration](grid.yaml) fixes a 4-input, 3-output Legendre layer of degree 3. Seed 42 fixes the coefficients of its 12 edges. The generator samples each edge over 8 segments of [-1, 1], with 32 samples per segment, asymmetric uint8 quantization and linear interpolation.

| Input ID | x0 | x1 | x2 | x3 |
|---|---:|---:|---:|---:|
| mixed_positions | -0.875 | 1.0 | 0.5645161271095276 | 0.0625 |
| lower_endpoint | -0.875 | -1.0 | 0.5645161271095276 | 0.0625 |
| swapped_inputs | 1.0 | -0.875 | 0.5645161271095276 | 0.0625 |

In `mixed_positions`, the four coordinates test a midpoint between samples, the upper endpoint, an interior sample and a point three quarters of the way between samples. `lower_endpoint` changes only the second coordinate to the lower endpoint. `swapped_inputs` exchanges the first two coordinates. [Input CSV](input.csv)

## Outputs before and after the fix

Each row compares one output for the same input vector. The Python reference is shared by both runs. Each delta is the absolute difference between the printed Wokwi and Python values. A row passes when its delta is at most 0.00001.

| Input ID | Output | Python LUT | Wokwi before | Delta before | Wokwi after | Delta after |
|---|---|---:|---:|---:|---:|---:|
| mixed_positions | y0 | 0.09732652 | 0.011473963 | 0.085852557 | 0.097326159 | 0.000000361 |
| mixed_positions | y1 | 0.0923316 | -0.234109208 | 0.326440808 | 0.092332512 | 0.000000912 |
| mixed_positions | y2 | -0.033376187 | -0.051082835 | 0.017706648 | -0.033375822 | 0.000000365 |
| lower_endpoint | y0 | 0.06383085 | 0.035141770 | 0.028689080 | 0.063829347 | 0.000001503 |
| lower_endpoint | y1 | 0.21845438 | -0.031809427 | 0.250263807 | 0.218456104 | 0.000001724 |
| lower_endpoint | y2 | 0.0710735 | 0.075040758 | 0.003967258 | 0.071074262 | 0.000000762 |
| swapped_inputs | y0 | 0.002920866 | 0.047399256 | 0.044478390 | 0.002922107 | 0.000001241 |
| swapped_inputs | y1 | 0.012955323 | 0.011762450 | 0.001192873 | 0.012956988 | 0.000001665 |
| swapped_inputs | y2 | 0.018303305 | 0.047806934 | 0.029503629 | 0.018302176 | 0.000001129 |

**Before the fix**, 0 of 9 outputs passed. The maximum delta was 0.326440808 for `mixed_positions / y1`. **After the fix**, 9 of 9 passed. The maximum delta was 0.000001724 for `lower_endpoint / y1`. [Python reference](results/python_reference.csv) · [Original serial log](results/wokwi-before.txt) · [Final serial log](results/wokwi-export-fix.txt) · [Before CSV](results/comparison-before.csv) · [After CSV](results/comparison-export-fix.csv)

### Why the outputs differed

Python assigned LUT rows by output and then by input. The original exporter preserved that order, while the firmware read block `input * out_dim + output`. For example, input 0 to output 1 occupied Python row 4, but the firmware read block 1. The [exporter](../../mcu_auto/scripts/gen_cases.py) now copies the samples, scales and offsets for that edge to block 1 of the header. The Python reference keeps using row 4. The final comparison uses the firmware's original indexing.

## Reproduce the run

Run the following commands from the LUT-KAN repository root.

1. Generate the case and compute the reference outputs using Python 3.11.15.

   ```powershell
   python mcu_auto/scripts/gen_cases.py --grid reproducibility/ivano-02/grid.yaml --suite ivano_02 --targets esp32c3 --out outputs/ivano-02/export-check --reference-inputs reproducibility/ivano-02/input.csv
   ```

   In the generated case directory, `include/case_layer.h` holds the model coefficients and LUT, `include/reference_inputs.h` holds the same float32 vectors used in Python, and [python_reference.csv](results/python_reference.csv) contains the three expected outputs per vector.

2. Build the firmware with PlatformIO Core 6.2.0. The generated `platformio.ini` selects the `esp32-c3-devkitm-1` board and the Arduino framework. This build used version 8.0.0 of the PlatformIO `espressif32` package.

   ```powershell
   python -m platformio run -d outputs/ivano-02/export-check/esp32c3/i4o3_jacobi_legendre_d3_L32_K8_linear_uint8_asymm_inlinspace_s42
   ```

3. Open an ESP32-C3 project in Wokwi using the [ESP32-C3 diagram.json](../../mcu_auto/targets/esp32c3/diagram.json). In the code editor, press **F1**, select **Upload Firmware and Start Simulation…**, and choose `.pio/build/mcu/firmware.bin` from the generated case. For each input vector, the serial monitor displays its ID followed by the three C++ outputs (`y0`, `y1`, `y2`). Compare each [serial log](results/wokwi-export-fix.txt) row starting with `LUT_REFERENCE` with the row for the same ID in [python_reference.csv](results/python_reference.csv).

This comparison checks numerical agreement for three fixed vectors on a simulated board. The measurements cover the floating-point LUT lookup with quantized samples. Physical latency, energy and person-detection accuracy are outside the scope of this test.
