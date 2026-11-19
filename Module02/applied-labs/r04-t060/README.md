# Applied Lab R04-T060: Microsoft Phi Model Family — Synthetic Manifest Selection & Applied Questions

## Overview

Deploying Small Language Models (SLMs) from the **Microsoft Phi model family** (such as Phi-3-mini, Phi-3-small, Phi-3-medium, or Phi-4) on resource-constrained edge devices requires deterministic matching of model resource footprints (RAM requirements and context window capacity) against host hardware constraints and application requirements.

This applied lab extends **Section 1: Microsoft Phi Model Family Fundamentals** at `Module02/01.PhiFamily.md`. It implements a deterministic local manifest selector that evaluates candidate models, admits eligible entries, generates actionable exclusion diagnostics, and answers three applied pedagogical questions: **predicting an output**, **diagnosing a failure**, and **choosing a boundary policy**.

### Core Pedagogical Principles
1. **Deterministic Constraint Matching**: Evaluates candidate models against host memory limits and task context demands using explicit inequalities (`required_ram_gb <= ram_budget_gb` and `max_context_length >= requested_context`).
2. **Actionable Exclusion Diagnostics**: When a model is disqualified, reports the exact resource violation (e.g., required RAM exceeds budget or context capacity is insufficient).
3. **Three Applied Questions**: Integrates three verifiable applied engineering questions:
   - *Predict an Output*: Predicts admission and exclusion under an expanded context workload.
   - *Diagnose a Failure*: Isolates the exact resource bottleneck in a low-memory deployment and prescribes actionable remedies.
   - *Choose a Boundary Policy*: Enforces an inclusive boundary admission policy (`<=` and `>=`) with factual rationale.
4. **Synthetic Teaching Fixtures**: Values are explicitly invented for instruction and do not represent claims about physical Microsoft Phi weights or hardware benchmarks.

---

## Canonical Contract Specification

Requirements aligned with Section 1 of `Module02/01.PhiFamily.md`:

### Candidate Manifest Fixtures
- **Fixture A**:
  - `model_id`: `"fixture-a"`
  - `name`: `"Synthetic Phi-Mini Teaching Variant A"`
  - `required_ram_gb`: `4.0` GB
  - `max_context_length`: `2048` tokens
- **Fixture B**:
  - `model_id`: `"fixture-b"`
  - `name`: `"Synthetic Phi-Medium Teaching Variant B"`
  - `required_ram_gb`: `8.0` GB
  - `max_context_length`: `4096` tokens

### Environmental Constraints
- `ram_budget_gb`: `6.0` GB
- `requested_context`: `1024` tokens

### Decision Matrix
| Model | Required RAM | Max Context | RAM Check (<= 6.0 GB) | Context Check (>= 1024 tokens) | Decision | Actionable Exclusion Diagnostic |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Fixture A** | 4.0 GB | 2048 | **PASS** (4.0 <= 6.0) | **PASS** (2048 >= 1024) | **ADMITTED** | N/A |
| **Fixture B** | 8.0 GB | 4096 | **FAIL** (8.0 > 6.0) | **PASS** (4096 >= 1024) | **EXCLUDED** | `Insufficient RAM: model requires 8.0 GB, but host budget is 6.0 GB.` |

**Outcome**: Admits **only Fixture A**.

---

## Three Applied Questions (Contribution Focus)

### Question 1: Predict an Output
- **Prompt**: Given an edge host configured with RAM budget 10.0 GB and requested context length 3000 tokens, which models from `[Fixture A (RAM4/context2048), Fixture B (RAM8/context4096)]` are admitted and which are excluded?
- **Factual Answer**: `{"admitted_ids": ["fixture-b"], "excluded_ids": ["fixture-a"]}`
- **Rationale**: Fixture A requires 4.0 GB RAM (within the 10.0 GB budget) but its maximum context window of 2048 tokens cannot accommodate the requested 3000 tokens, leading to exclusion. Fixture B requires 8.0 GB RAM (within budget) and supports 4096 tokens (exceeding 3000 tokens), satisfying both constraints.
- **Executable Check**: `check_predict_output()` executes the selector under this scenario and asserts that only Fixture B is admitted.

### Question 2: Diagnose a Failure
- **Prompt**: When evaluating `[Fixture A, Fixture B]` on a constrained device with RAM budget 3.0 GB and requested context 1024 tokens, both models fail admission. What is the specific resource bottleneck causing Fixture A's disqualification, and what actionable remedy resolves it?
- **Factual Answer**:
  - Failing model: `fixture-a`
  - Primary bottleneck: `RAM` (4.0 GB required vs 3.0 GB budget)
  - Diagnostic reason: `"Insufficient RAM: model requires 4.0 GB, but host budget is 3.0 GB."`
  - Actionable remedy: Increase host RAM allocation to at least 4.0 GB or apply INT4 quantization to reduce memory footprint below 3.0 GB.
- **Rationale**: The memory admission check enforces `required_ram_gb <= ram_budget_gb`. Fixture A requires 4.0 GB, exceeding available host memory by 1.0 GB. Although its context capacity (2048 tokens) satisfies the 1024-token requirement, memory failure causes immediate exclusion.
- **Executable Check**: `check_diagnose_failure()` executes the selector under budget 3.0 GB and verifies the diagnostic message.

### Question 3: Choose a Boundary Policy
- **Prompt**: For an edge device where a candidate model's resource requirements match the environment constraints exactly (`required_ram_gb == ram_budget_gb` and `max_context_length == requested_context`), which boundary policy should the selector enforce: inclusive boundary admission (`<=` and `>=`) or strict inequality (`<` and `>`)?
- **Factual Answer**: `INCLUSIVE_BOUNDARY_ADMISSION` (`required_ram_gb <= ram_budget_gb` and `max_context_length >= requested_context`), resulting in `ADMITTED`.
- **Rationale**: Edge resource envelopes define the upper ceiling of available physical RAM and the lower floor of required context depth. A model requiring exactly the allocated memory (without exceeding it) and providing exactly the requested context operates safely within specification. Strict inequality would prematurely reject models that fit within the available envelope.
- **Executable Check**: `check_choose_boundary_policy()` evaluates a boundary model (RAM 6.0 GB, context 1024) under budget 6.0 GB and context 1024, confirming admission.

---

## Unestablished Real-Service Behaviors

To maintain clear pedagogical boundaries, this offline mock explicitly declares behaviors that it does **not** establish:

1. **Host Memory Probing**: Does not query physical host memory registers, OS virtual swap, or unified memory architectures.
2. **Model Weight Loading**: Does not download, load, or evaluate real Microsoft Phi model weights (Phi-1, Phi-2, Phi-3, Phi-4).
3. **Inference Throughput**: Does not measure real-world inference throughput (tokens/second), time-to-first-token, or GPU latency.
4. **Hardware Driver Contexts**: Does not allocate physical GPU VRAM, CUDA buffers, or NPU runtime execution contexts.
5. **Model Accuracy & Reasoning**: Does not validate model reasoning accuracy, benchmark scores (MMLU, GSM8K), or response quality.

---

## Concept Mapping to Module 02 (01.PhiFamily.md)

| Lab Component | Lesson Concept in Module02/01.PhiFamily.md | Pedagogical Purpose |
| :--- | :--- | :--- |
| `required_ram_gb` (4.0 GB vs 8.0 GB) | Section 1 Microsoft Phi Model Family Fundamentals (Phi-3-mini vs Phi-3-medium) | Illustrates edge hardware footprint planning across compact SLM tiers. |
| `max_context_length` (2048 vs 4096 tokens) | Section 1 Architectural Innovations & Context Window Scaling | Demonstrates matching task prompt lengths to model context capacity. |
| Actionable Exclusion Diagnostics | Best Practices: Consider Hardware & Deployment Planning | Provides distinct explanations detailing why candidate models exceed host bounds. |
| Three Applied Pedagogical Questions | Practical Decision-Making Matrix for Phi Variant Selection | Reinforces prediction, failure diagnosis, and boundary policy evaluation. |
| Inclusive Boundary Admission Policy | Optimization Techniques for Resource-Constrained Devices | Ensures boundary-case resource envelope utilization without false rejections. |

---

## File Structure

- `example.py`: Core `PhiModelManifestSelector`, `ModelEntry`, canonical fixtures, and the three applied questions engine.
- `test_example.py`: 12 automated unit tests verifying canonical selection, exclusion diagnostics, all three applied questions, boundary conditions, and teaching boundaries.
- `README.md`: Technical documentation, decision matrix, applied questions rationales, and concept mapping.

---

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Unit Test Suite
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t060 -p "test_*.py"
```
