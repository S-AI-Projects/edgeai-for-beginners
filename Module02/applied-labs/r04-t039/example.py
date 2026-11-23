"""
Symmetric Signed-Int8 Quantizer and Scenario Assessment.

Implements a symmetric signed-int8 teaching quantizer with positive scale,
clipping to [-127, 127], and float dequantization reconstruction.
Contracts:
  - Values [-1.0, 0.0, 1.0] with scale=0.1 yield [-10, 0, 10] and reconstruct exactly.
  - Value 20.0 with scale=0.1 yields 200, which clips to 127.
  - Nonpositive scale (<= 0) is rejected with ValueError.
Includes three applied questions (predict output, diagnose failure, boundary policy).
"""

from typing import List, Dict, Any, Union
import json


class SymmetricInt8Quantizer:
    """
    Symmetric signed int8 quantizer.
    Quantization range: [-127, 127]
    Formula:
      q = clip(round(x / scale), -127, 127)
      x_recon = q * scale
    """
    def __init__(self, scale: float):
        if not isinstance(scale, (int, float)) or isinstance(scale, bool) or scale <= 0:
            raise ValueError(f"Scale must be a positive numeric value, got: {scale}")
        self.scale = float(scale)

    def quantize(self, val: float) -> int:
        raw = round(val / self.scale)
        return max(-127, min(127, raw))

    def dequantize(self, q_val: int) -> float:
        return round(q_val * self.scale, 8)

    def quantize_array(self, values: List[float]) -> List[int]:
        return [self.quantize(v) for v in values]

    def reconstruct_array(self, q_values: List[int]) -> List[float]:
        return [self.dequantize(q) for q in q_values]


APPLIED_QUESTIONS = [
    {
        "id": "Q1_predict_output",
        "question": "What is the quantized int8 value and reconstructed float for input 5.0 with scale 0.1?",
        "answer": {"quantized": 50, "reconstructed": 5.0},
        "rationale": "5.0 / 0.1 = 50. Since 50 falls inside [-127, 127], it does not clip. Dequantizing 50 * 0.1 yields exactly 5.0.",
    },
    {
        "id": "Q2_diagnose_failure",
        "question": "Why does initializing the quantizer with scale = -0.5 fail?",
        "answer": "REJECTED_NONPOSITIVE_SCALE",
        "rationale": "Scale factors in symmetric quantization represent positive step size ratios (delta = range / steps). A negative or zero scale is mathematically meaningless for distance scaling and is explicitly rejected.",
    },
    {
        "id": "Q3_boundary_policy",
        "question": "Why does symmetric int8 clamp to [-127, 127] instead of standard two's complement [-128, 127]?",
        "answer": "SYMMETRIC_ZERO_REPRESENTATION",
        "rationale": "Symmetric signed quantization ensures exact symmetry around 0 without a zero-point offset: -q maps to -x and +q maps to +x with identical saturation thresholds on both positive and negative poles.",
    }
]


def run_demo() -> Dict[str, Any]:
    quantizer = SymmetricInt8Quantizer(scale=0.1)

    # Contract 1: [-1.0, 0.0, 1.0] -> [-10, 0, 10] and exact reconstruction
    canon_in = [-1.0, 0.0, 1.0]
    canon_q = quantizer.quantize_array(canon_in)
    canon_recon = quantizer.reconstruct_array(canon_q)

    # Contract 2: 20.0 clips to 127
    clip_q = quantizer.quantize(20.0)

    # Contract 3: nonpositive scale rejected
    scale_err = None
    try:
        SymmetricInt8Quantizer(scale=0.0)
    except ValueError as e:
        scale_err = str(e)

    return {
        "canon_input": canon_in,
        "canon_quantized": canon_q,
        "canon_reconstructed": canon_recon,
        "clip_value_20_quantized": clip_q,
        "nonpositive_scale_error": scale_err,
        "applied_questions": APPLIED_QUESTIONS
    }


if __name__ == "__main__":
    out = run_demo()
    print(json.dumps(out, indent=2))
