# Applied Lab R04-T057: Gemma Family Synthetic Model-Manifest Selection — Worked Example & Regression Checks

## Overview

Selecting the appropriate Small Language Model (SLM) for edge deployment requires matching model resource footprints (RAM footprint, context window limits) against host hardware constraints and application requirements.

This applied lab extends **Section 3: Gemma Family Fundamentals** at `Module02/03.GemmaFamily.md`. It implements a deterministic local manifest selector that evaluates candidate models, admits compliant models, and generates explicit failure diagnostics for excluded models.

### Core Pedagogical Principles
1. **Deterministic Constraint Matching**: Evaluates candidate models against explicit host memory limits and task context demands.
2. **Actionable Exclusion Diagnostics**: When a model is disqualified, reports the exact resource violation (e.g. required RAM exceeds budget or context capacity is insufficient).
3. **Worked Input-to-Output Demonstration**: Provides a complete, human-readable walkthrough from input manifest to output decision report.
4. **Regression-Tested Contract**: Verifies that the exact canonical fixture admits only Fixture A under the specified constraints.
5. **Synthetic Teaching Fixtures**: Values are explicitly invented for instruction and do not represent claims about physical Google Gemma models.

---

## Contract Specification

Requirements aligned with Section 3 of `Module02/03.GemmaFamily.md`:

### Candidate Manifest Fixtures
- **Fixture A**:
  - `model_id`: `"fixture-a"`
  - `required_ram_gb`: `4.0` GB
  - `max_context_length`: `2048` tokens
- **Fixture B**:
  - `model_id`: `"fixture-b"`
  - `required_ram_gb`: `8.0` GB
  - `max_context_length`: `4096` tokens

### Environmental Constraints
- `ram_budget_gb`: `6.0` GB
- `requested_context`: `1024` tokens

### Canonical Decision Contract
| Model | Required RAM | Max Context | Host RAM Check (<= 6.0 GB) | Context Check (>= 1024 tokens) | Result | Exclusion Explanation |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Fixture A** | 4.0 GB | 2048 | PASS (4.0 <= 6.0) | PASS (2048 >= 1024) | **ADMITTED** | N/A |
| **Fixture B** | 8.0 GB | 4096 | **FAIL** (8.0 > 6.0) | PASS (4096 >= 1024) | **EXCLUDED** | `Insufficient RAM: model requires 8.0 GB, but host budget is 6.0 GB.` |

**Outcome**: Admits **only Fixture A**.

---

## Worked Input-to-Output Walkthrough

```
1. INPUT SPECIFICATION
   - Host Budget: RAM = 6.0 GB, Requested Context = 1024 tokens.
   - Manifest:
     * Fixture A: RAM = 4.0 GB, Context = 2048 tokens
     * Fixture B: RAM = 8.0 GB, Context = 4096 tokens

2. EVALUATION PIPELINE
   - Evaluating Fixture A:
       * 4.0 GB <= 6.0 GB -> PASS
       * 2048 >= 1024 tokens -> PASS
       => Verdict: ADMITTED
   - Evaluating Fixture B:
       * 8.0 GB <= 6.0 GB -> FAIL (exceeds budget by 2.0 GB)
       * 4096 >= 1024 tokens -> PASS
       => Verdict: EXCLUDED (Insufficient RAM)

3. OUTPUT REPORT
   - Admitted IDs: ["fixture-a"]
   - Excluded IDs: ["fixture-b"]
   - Exclusion Diagnostics:
       [fixture-b] Insufficient RAM: model requires 8.0 GB, but host budget is 6.0 GB.
```

---

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly declares behaviors that it does **not** establish:

1. **Physical Host Memory Probing**: Does not inspect OS-level virtual memory, swap partitions, or unified memory architectures.
2. **Model Weight Loading**: Does not download, parse, or verify real Gemma model weights (e.g. Gemma 2 2B, 9B, 27B) or evaluate GGUF/ONNX headers.
3. **Kernel Memory Allocations**: Does not allocate GPU VRAM, CUDA unified buffers, or configure runtime KV caches.
4. **Hardware Performance Claims**: Does not establish real-world inference throughput, latency, or model accuracy.
5. **Synthetic Nature**: Values are invented teaching fixtures designed solely for deterministic constraint verification.

---

## Concept Mapping to Module 02 (Section 3)

| Selector Component | Lesson Concept in Module02/03.GemmaFamily.md | Pedagogical Purpose |
| :--- | :--- | :--- |
| `required_ram_gb` (4 GB vs 8 GB) | Model Size and Deployment Options (Gemma 2B/4B edge vs 8B/27B workstation sizes) | Illustrates memory footprint planning for constrained edge hardware. |
| `max_context_length` (2048 vs 4096 tokens) | Context Window Expansion Innovations (8K vs 128K context capabilities) | Ensures model context window accommodates workload document lengths. |
| `ram_budget_gb` & `requested_context` | Key Deployment Requirements (Edge Deployment & Cost Effectiveness) | Defines explicit environmental resource envelopes before model loading. |
| Explicit Exclusion Reporting | Deployment Planning and Troubleshooting Best Practices | Provides deterministic, actionable explanations when a model is disqualified. |
| Worked Input-to-Output Regression Example | Practical Decision-Making Matrix for Gemma Variant Selection | Demonstrates regression-tested step-by-step evaluation from inputs to outputs. |

---

## File Structure

- `example.py`: Core `ModelManifestSelector`, `ModelEntry`, `SelectionResult`, and `explain_worked_example()` workflow.
- `test_example.py`: 11 unit tests covering exact worked example regression, boundary conditions, argument validations, and unestablished behavior declarations.
- `README.md`: Technical documentation, decision matrix, and concept mapping.

---

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t057 -p "test_*.py"
```
