# Applied Lab R04-T053: Symmetric Signed-INT8 Quantizer — Compare Two Approaches

## Overview

In modern low-bit neural network architectures like Microsoft's BitNET model family (e.g. BitNet b1.58), activation quantization commonly utilizes symmetric signed 8-bit integers mapped to the range `[-127, 127]`.

This lab implements a deterministic, local **Symmetric Signed-INT8 Teaching Quantizer** and directly compares two independent calculation approaches on identical inputs:
1. **Approach A (Direct Object-Oriented)**: `SymmetricInt8Quantizer` class managing scaling, boundary clamping, dequantization, and error metrics.
2. **Approach B (Simpler Reference Calculation)**: Pure mathematical functional pipeline `reference_pipeline` implementing single-pass rounding, clamping, and multiplication.

## Contract Specification

1. **Symmetric Int8 Range**: Quantized values strictly adhere to `[-127, 127]`.
2. **Exact Reconstruction Fixture**:
   - Inputs: `[-1.0, 0.0, 1.0]` with `scale = 0.1`
   - Quantized output: `[-10, 0, 10]`
   - Reconstructed output: `[-1.0, 0.0, 1.0]` (0.0 reconstruction error)
3. **Clipping Boundary**:
   - Value `20.0` with `scale = 0.1` ($20.0 / 0.1 = 200$) saturates at the upper bound `127`, reconstructing to `12.7`.
   - Value `-20.0` with `scale = 0.1` saturates at `-127`, reconstructing to `-12.7`.
4. **Scale Validation**:
   - Nonpositive scale values (`scale <= 0`) are rejected with `ValueError`.
5. **Two-Approach Equivalence**:
   - Direct and reference implementations produce identical quantized integers and reconstructed floats across identical test inputs.

## Two-Approach Comparison Table

| Input ($x$) | Scale ($s$) | Scaled ($x/s$) | Direct Quantized | Reference Quantized | Clipped? | Direct Recon | Reference Recon | Quantization Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `-1.0` | `0.1` | `-10.0` | `-10` | `-10` | No | `-1.0` | `-1.0` | `0.0` |
| `0.0` | `0.1` | `0.0` | `0` | `0` | No | `0.0` | `0.0` | `0.0` |
| `1.0` | `0.1` | `10.0` | `10` | `10` | No | `1.0` | `1.0` | `0.0` |
| `12.7` | `0.1` | `127.0` | `127` | `127` | No | `12.7` | `12.7` | `0.0` |
| `20.0` | `0.1` | `200.0` | `127` | `127` | **Yes** | `12.7` | `12.7` | `7.3` |
| `-20.0`| `0.1` | `-200.0`| `-127` | `-127` | **Yes** | `-12.7` | `-12.7` | `7.3` |

## Concept Mapping to BitNET Fundamentals

| Component | BitNET Model Family Concept (Module 02) |
| :--- | :--- |
| `scale` | Dynamic range scale factor (e.g. per-token absmax scaling for activations) |
| `[-127, 127]` | Symmetric signed int8 dynamic range preserving zero symmetry |
| `clipping` | Saturated outlier handling preventing numerical overflow in integer dot-products |
| `reconstruction error`| Precision tradeoff defining the quantization error budget in edge inference |
| `approach comparison`| Algorithmic verification between object-oriented engine and reference arithmetic |

## Scope, Limitations & Simulation Notice

> [!NOTE] Teaching Approximation & Simulation Notice
> This fixture illustrates symmetric signed-int8 quantization and clipping semantics using Python standard library scalar operations.
> 
> Production BitNET inference engines (e.g. `bitnet.cpp`) leverage hardware-accelerated SIMD/AVX kernels, fused BitLinear matrix multiplications, and ternary weight multiplication.
> 
> This is a minimal local verification fixture: no model weights, GPU hardware, or external frameworks (PyTorch/ONNX) are required. The example makes no unsupported claims regarding real hardware latency or trained-model inference capabilities.

## File Structure

- `example.py`: Core `SymmetricInt8Quantizer`, reference functions, and comparison logic.
- `test_example.py`: 10 automated unit tests covering exact reconstruction, clipping, error handling, and approach comparison.
- `README.md`: Technical documentation, contract specification, and comparison table.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t053 -p "test_*.py"
```
