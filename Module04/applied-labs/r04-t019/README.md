# R04-T019 - Quantization Error Budget: Evaluation Experiment

Companion applied lab to [Module04/01.Introduce.md](../../01.Introduce.md) ("Section 1: Model Format Conversion and Quantization Foundations - Precision Classification Framework").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
In EdgeAI model compression, 8-bit integer quantization (INT8) reduces floating-point parameter representations into compact 8-bit integers. A symmetric signed INT8 scheme maps continuous floats into the range $[-127, 127]$ using a positive scaling factor:
$$q = \text{clip}\left(\text{round}\left(\frac{x}{\text{scale}}\right), -127, 127\right)$$
$$\hat{x} = q \cdot \text{scale}$$

This lab demonstrates:
1. **Symmetric Clamping**: Values are rounded and clamped strictly to $[-127, 127]$.
2. **Exact Small-Value Reconstruction**: For values aligned with the scale step, reconstruction is mathematically exact.
3. **Clipping Saturation**: Values exceeding the dynamic range ($x > 127 \times \text{scale}$) saturate at $127$.
4. **Scale Validation**: Scale must be strictly positive; nonpositive scales ($\le 0$) are rejected (`INVALID_SCALE`).
5. **Precision vs Dynamic Range Trade-off**: Compares 3 controlled configurations:
   * **Fine Scale ($0.01$)**: High resolution for small values, but clips out-of-range inputs.
   * **Balanced Scale ($0.1$)**: Balanced precision with moderate dynamic range $[-12.7, 12.7]$.
   * **Coarse Scale ($1.0$)**: Broad dynamic range $[-127, 127]$ with zero clipping, but coarser rounding increments.

### Scope and Limitations
* **Teaching Model Only**: Evaluates scalar/array quantization arithmetic. It **does not** claim accuracy or perplexity results on real trained weights or complex neural architectures.
* **Prerequisites**: Python 3 standard library only.

---

## 2. Canonical Task Fixture

* Input: `[-1, 0, 1]` with `scale = 0.1` $\rightarrow$ Quantized: `[-10, 0, 10]`, Reconstructed: `[-1.0, 0.0, 1.0]` (exact).
* Input: `20` with `scale = 0.1` $\rightarrow$ Clamped: `127`, Reconstructed: `12.7`.
* Input: Scale $\le 0$ $\rightarrow$ Rejected with `INVALID_SCALE`.

---

## 3. Run and Verify

```bash
python3 Module04/applied-labs/r04-t019/example.py
python3 -m unittest discover -s Module04/applied-labs/r04-t019 -p "test_*.py"
```
Ran 10 tests in ~0.001s, OK.
