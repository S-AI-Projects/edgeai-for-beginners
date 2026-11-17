"""
R04-T019: Quantization Error Budget - Evaluation Experiment
Companion applied lab for Module04/01.Introduce.md.

Demonstrates symmetric signed-int8 teaching quantization and reconstruction:
- Formula: q = clip(round(x / scale), -127, 127)
- Reconstruction: x_reconstructed = q * scale
- Strict positive scale enforcement: scale <= 0 is rejected (INVALID_SCALE).
- Canonical fixture:
    Values [-1, 0, 1] with scale=0.1 -> quantized [-10, 0, 10], reconstructs exactly.
    Value 20 with scale=0.1 -> clips to 127, reconstructs to 12.7.
- Compares 3 controlled configurations to evaluate precision vs clipping trade-offs.

Prerequisites: Python 3 standard library only.
"""

from typing import Any, Dict, List, Tuple, Union


class QuantizationError(Exception):
    """Raised when scale or input values violate quantization contract."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def quantize_value(x: Union[int, float], scale: float) -> int:
    """Quantizes a single scalar to symmetric int8 [-127, 127]."""
    if not isinstance(scale, (int, float)) or scale <= 0.0:
        raise QuantizationError("INVALID_SCALE", f"Scale must be a positive number, got: {scale!r}")
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise QuantizationError("INVALID_INPUT", f"Value must be a number, got: {type(x).__name__}")

    raw_q = round(x / scale)
    return max(-127, min(127, raw_q))


def dequantize_value(q: int, scale: float) -> float:
    """Reconstructs float value from quantized int8."""
    return round(q * scale, 10)


def quantize_and_reconstruct(
    values: List[Union[int, float]],
    scale: float
) -> Dict[str, Any]:
    """
    Quantizes a sequence of float values and reconstructs them,
    reporting quantized ints, reconstructed floats, and errors.
    """
    if not isinstance(values, (list, tuple)):
        raise QuantizationError("INVALID_INPUT", f"Values must be a list or tuple, got {type(values).__name__}")
    if not isinstance(scale, (int, float)) or scale <= 0.0:
        raise QuantizationError("INVALID_SCALE", f"Scale must be a positive number, got: {scale!r}")

    quantized = []
    reconstructed = []
    clipping_count = 0
    errors = []

    for v in values:
        q = quantize_value(v, scale)
        if abs(q) == 127 and abs(v / scale) > 127:
            clipping_count += 1
        rec = dequantize_value(q, scale)
        quantized.append(q)
        reconstructed.append(rec)
        errors.append(abs(v - rec))

    mae = sum(errors) / len(errors) if errors else 0.0
    mse = sum(e ** 2 for e in errors) / len(errors) if errors else 0.0

    return {
        "scale": scale,
        "input_values": list(values),
        "quantized": quantized,
        "reconstructed": reconstructed,
        "clipping_count": clipping_count,
        "mean_absolute_error": round(mae, 6),
        "mean_squared_error": round(mse, 6),
    }


def compare_three_configurations() -> List[Dict[str, Any]]:
    """
    Compares 3 controlled configurations over test data [-20, -1, 0, 1, 20]:
    - Config A (Fine scale 0.01): High resolution for tiny values, heavy clipping on 20.
    - Config B (Balanced scale 0.1): Balanced resolution, moderate range [-12.7, 12.7].
    - Config C (Coarse scale 1.0): Zero clipping for all values, but coarser rounding resolution.
    """
    dataset = [-20.0, -1.0, 0.0, 1.0, 20.0]
    configs = [
        {"name": "Config A (Fine: scale=0.01)", "scale": 0.01},
        {"name": "Config B (Balanced: scale=0.1)", "scale": 0.1},
        {"name": "Config C (Coarse: scale=1.0)", "scale": 1.0},
    ]

    results = []
    for cfg in configs:
        eval_res = quantize_and_reconstruct(dataset, cfg["scale"])
        results.append({
            "config": cfg["name"],
            "scale": cfg["scale"],
            "clipping_count": eval_res["clipping_count"],
            "mae": eval_res["mean_absolute_error"],
            "mse": eval_res["mean_squared_error"],
        })
    return results


def run_concept_example() -> Dict[str, Any]:
    """Runs the canonical fixture scenarios."""
    # 1. Canonical [-1, 0, 1] with scale=0.1
    canonical_res = quantize_and_reconstruct([-1.0, 0.0, 1.0], 0.1)

    # 2. Canonical value 20 with scale=0.1 (clipping to 127)
    clip_q = quantize_value(20.0, 0.1)
    clip_rec = dequantize_value(clip_q, 0.1)

    # 3. Nonpositive scale rejection
    rejected_zero = False
    rejected_negative = False
    try:
        quantize_value(1.0, 0.0)
    except QuantizationError as exc:
        if exc.code == "INVALID_SCALE":
            rejected_zero = True

    try:
        quantize_value(1.0, -0.1)
    except QuantizationError as exc:
        if exc.code == "INVALID_SCALE":
            rejected_negative = True

    # 4. Comparative evaluation across 3 configurations
    comparisons = compare_three_configurations()

    return {
        "canonical_quantized": canonical_res["quantized"],
        "canonical_reconstructed": canonical_res["reconstructed"],
        "canonical_exact": canonical_res["reconstructed"] == [-1.0, 0.0, 1.0],
        "clip_quantized": clip_q,
        "clip_reconstructed": clip_rec,
        "rejected_zero": rejected_zero,
        "rejected_negative": rejected_negative,
        "comparisons": comparisons,
    }


if __name__ == "__main__":
    res = run_concept_example()
    print("=== Symmetric Signed-Int8 Quantizer ===")
    print(f"Values [-1, 0, 1], scale=0.1 -> quantized={res['canonical_quantized']}")
    print(f"Reconstructed: {res['canonical_reconstructed']} (Exact: {res['canonical_exact']})")
    print(f"Value 20, scale=0.1 -> quantized={res['clip_quantized']} (reconstructed: {res['clip_reconstructed']})")
    print(f"Nonpositive scale rejected: scale=0 ({res['rejected_zero']}), scale=-0.1 ({res['rejected_negative']})")
    print("\n--- 3-Configuration Comparison ---")
    for c in res["comparisons"]:
        print(f"{c['config']}: Clipping Count={c['clipping_count']}, MAE={c['mae']}, MSE={c['mse']}")
    print("\n[NOTE] Pedagogical contract fixture. Does not establish accuracy on real trained model weights.")
