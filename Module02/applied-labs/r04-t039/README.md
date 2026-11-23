# R04-T039: Quantization Error Budget Scenario Assessment

## Overview
This lab extends `Module02/04.BitNETFamily.md` by demonstrating a symmetric signed-int8 teaching quantizer with clipping and reconstruction.

### Quantization Contracts
- Quantization Range: $[-127, 127]$
- Formula: $q = \text{clip}\left(\text{round}\left(\frac{x}{\text{scale}}\right), -127, 127\right)$
- Reconstruction: $\hat{x} = q \times \text{scale}$
- Input $[-1.0, 0.0, 1.0]$ with $\text{scale}=0.1$ yields $[-10, 0, 10]$ and reconstructs exactly.
- Saturation: $x = 20.0$ with $\text{scale}=0.1$ produces $200$, clamped to $127$.
- Nonpositive scale ($\le 0$) is rejected.

### Applied Questions
The lab includes three applied questions in `questions.json` and executable assertions covering output prediction, failure diagnosis, and symmetric boundary policies.

## Execution
```bash
python3 Module02/applied-labs/r04-t039/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t039 -p "test_*.py"
```
