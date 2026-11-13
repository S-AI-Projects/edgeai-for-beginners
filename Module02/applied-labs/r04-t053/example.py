#!/usr/bin/env python3
"""
Symmetric Signed-INT8 Teaching Quantizer: Compare Two Approaches (R04-T053)
Module 02: BitNET Family Fundamentals (04.BitNETFamily.md)

Concept:
In low-bit architectures such as Microsoft's BitNET model family (e.g. BitNet b1.58),
activation quantization commonly utilizes symmetric signed 8-bit quantization
scaled to the range [-127, 127]. Quantization projects continuous floating-point
activations into discrete integer buckets using a positive scale factor, clipping
values that exceed dynamic range, and dequantizing back to floating-point representation.

Focus:
Implement a symmetric signed-int8 teaching quantizer with clipping to [-127, 127]
and compare the direct object-oriented implementation with a simpler independent
reference calculation on identical inputs.

Pedagogical Notice:
This local fixture is a teaching approximation of symmetric INT8 quantization.
It operates on Python scalar floats without GPU acceleration, CUDA kernels,
or quantized BitLinear tensor runtime dependencies.
"""

from typing import Any, Dict, List, Sequence, Tuple


class SymmetricInt8Quantizer:
    """Direct object-oriented symmetric signed-int8 quantizer with clipping to [-127, 127].

    Attributes:
        scale: Positive float scaling factor.
        min_bound: Lower integer clipping boundary (-127).
        max_bound: Upper integer clipping boundary (127).
    """

    MIN_INT8: int = -127
    MAX_INT8: int = 127

    def __init__(self, scale: float) -> None:
        """Initialize quantizer with a positive scale factor.

        Args:
            scale: Positive floating-point scale factor.

        Raises:
            ValueError: If scale is nonpositive (<= 0).
        """
        if scale <= 0:
            raise ValueError(f"Scale must be a positive number (> 0), got: {scale}")
        self.scale = float(scale)
        self.min_bound = self.MIN_INT8
        self.max_bound = self.MAX_INT8

    def quantize(self, value: float) -> int:
        """Quantize a float value to signed int8 in range [-127, 127].

        Args:
            value: Float value to quantize.

        Returns:
            Quantized integer clipped to [-127, 127].
        """
        scaled = value / self.scale
        rounded = int(round(scaled))
        return max(self.min_bound, min(self.max_bound, rounded))

    def dequantize(self, q_value: int) -> float:
        """Reconstruct float approximation from quantized integer.

        Args:
            q_value: Quantized integer in range [-127, 127].

        Returns:
            Dequantized floating-point value.

        Raises:
            ValueError: If q_value is outside [-127, 127].
        """
        if not (self.min_bound <= q_value <= self.max_bound):
            raise ValueError(f"Quantized value {q_value} out of bounds [{self.min_bound}, {self.max_bound}]")
        return round(q_value * self.scale, 8)

    def quantize_sequence(self, values: Sequence[float]) -> List[int]:
        """Quantize an iterable sequence of float values."""
        return [self.quantize(v) for v in values]

    def dequantize_sequence(self, q_values: Sequence[int]) -> List[float]:
        """Dequantize an iterable sequence of quantized integers."""
        return [self.dequantize(q) for q in q_values]

    def process(self, values: Sequence[float]) -> Dict[str, Any]:
        """Full quantization, reconstruction, and error analysis pipeline."""
        quantized = self.quantize_sequence(values)
        reconstructed = self.dequantize_sequence(quantized)
        errors = [round(abs(orig - recon), 8) for orig, recon in zip(values, reconstructed)]
        clipped = [abs(orig / self.scale) > self.MAX_INT8 for orig in values]

        return {
            "scale": self.scale,
            "inputs": list(values),
            "quantized": quantized,
            "reconstructed": reconstructed,
            "errors": errors,
            "max_error": max(errors) if errors else 0.0,
            "clipped_flags": clipped,
            "clipped_count": sum(clipped),
        }


# =====================================================================
# Approach B: Simpler Independent Reference Calculation
# =====================================================================

def reference_quantize(value: float, scale: float) -> int:
    """Pure mathematical reference quantization: round(val / scale) clipped to [-127, 127]."""
    if scale <= 0:
        raise ValueError("Scale must be positive")
    return max(-127, min(127, int(round(value / scale))))


def reference_dequantize(q_val: int, scale: float) -> float:
    """Pure mathematical reference reconstruction: q_val * scale."""
    return round(q_val * scale, 8)


def reference_pipeline(values: Sequence[float], scale: float) -> Tuple[List[int], List[float]]:
    """Compute quantized ints and reconstructed floats via reference functions."""
    q_vals = [reference_quantize(v, scale) for v in values]
    r_vals = [reference_dequantize(q, scale) for q in q_vals]
    return q_vals, r_vals


# =====================================================================
# Two-Approach Comparison Framework
# =====================================================================

def compare_approaches(values: Sequence[float], scale: float) -> Dict[str, Any]:
    """Compare direct quantizer against reference calculation on identical inputs.

    Args:
        values: Sequence of input float values.
        scale: Positive scale factor.

    Returns:
        Structured dictionary comparing outputs of both approaches.
    """
    direct_quantizer = SymmetricInt8Quantizer(scale=scale)
    direct_result = direct_quantizer.process(values)

    ref_q, ref_recon = reference_pipeline(values, scale)

    # Detailed row-by-row comparison
    comparison_table = []
    all_match = True
    for orig, q_dir, q_ref, r_dir, r_ref in zip(
        values,
        direct_result["quantized"],
        ref_q,
        direct_result["reconstructed"],
        ref_recon,
    ):
        q_match = (q_dir == q_ref)
        r_match = (r_dir == r_ref)
        if not (q_match and r_match):
            all_match = False
        comparison_table.append({
            "input": orig,
            "direct_q": q_dir,
            "ref_q": q_ref,
            "q_match": q_match,
            "direct_recon": r_dir,
            "ref_recon": r_ref,
            "recon_match": r_match,
            "clipped": abs(orig / scale) > 127,
        })

    return {
        "scale": scale,
        "identical_quantization": direct_result["quantized"] == ref_q,
        "identical_reconstruction": direct_result["reconstructed"] == ref_recon,
        "all_match": all_match,
        "direct": {
            "quantized": direct_result["quantized"],
            "reconstructed": direct_result["reconstructed"],
            "max_error": direct_result["max_error"],
        },
        "reference": {
            "quantized": ref_q,
            "reconstructed": ref_recon,
        },
        "comparison_table": comparison_table,
    }


def explain_mapping() -> Dict[str, str]:
    """Map public quantizer fields to BitNET quantization concepts."""
    return {
        "scale": "Scaling factor determining dynamic range resolution (similar to absmax scaling in BitNet)",
        "quantize": "Mapping continuous float activations into signed int8 buckets [-127, 127]",
        "dequantize": "Reconstructing float activation values for downstream computation",
        "clipping": "Saturation behavior at boundaries [-127, 127] when activation exceeds dynamic range",
        "reconstruction_error": "Discretization noise (|x - recon(x)|) defining quantization error budget",
        "approach_comparison": "Validating direct implementation against independent reference arithmetic",
    }


def main() -> None:
    """Run CLI demonstration comparing direct quantizer with reference calculation."""
    print("=" * 70)
    print("Symmetric Signed-INT8 Quantizer - Two Approaches Comparison (R04-T053)")
    print("=" * 70)

    # Contract Fixture 1: [-1, 0, 1] with scale=0.1
    inputs_exact = [-1.0, 0.0, 1.0]
    scale_1 = 0.1
    comp_1 = compare_approaches(inputs_exact, scale=scale_1)

    print(f"\n1. Exact Reconstruction Fixture (inputs={inputs_exact}, scale={scale_1}):")
    print(f"   Direct Quantized:    {comp_1['direct']['quantized']}")
    print(f"   Reference Quantized: {comp_1['reference']['quantized']}")
    print(f"   Direct Recon:        {comp_1['direct']['reconstructed']}")
    print(f"   Reference Recon:     {comp_1['reference']['reconstructed']}")
    print(f"   Approaches Agree:    {comp_1['all_match']}")

    # Contract Fixture 2: Boundary Clipping (value=20, scale=0.1)
    inputs_clip = [20.0, -20.0, 12.7]
    comp_2 = compare_approaches(inputs_clip, scale=scale_1)
    print(f"\n2. Clipping Fixture (inputs={inputs_clip}, scale={scale_1}):")
    for row in comp_2["comparison_table"]:
        print(f"   Value {row['input']:>5} -> Quantized: {row['direct_q']:>4} (Clipped: {row['clipped']}), Recon: {row['direct_recon']:>5}")

    # Contract Fixture 3: Negative/Zero Scale Rejection
    print("\n3. Error Handling (Nonpositive Scale):")
    for invalid_s in [0.0, -0.1]:
        try:
            SymmetricInt8Quantizer(scale=invalid_s)
        except ValueError as e:
            print(f"   Scale {invalid_s} correctly rejected: {e}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
