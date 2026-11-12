# Applied Lab R04-T051: Token-Budget Preflight — Containerized Cloud Deployment

## Overview

In containerized cloud deployments of Small Language Models (SLMs) such as Microsoft Phi-4-mini-instruct (e.g., via vLLM or ONNX Runtime containers), inference services operate under strict resource constraints and preconfigured context window budgets (such as `--max-model-len 4096`).

Dispatching unvalidated or oversized prompts to containerized endpoints can cause:
- Context limit overflow errors
- Degraded reasoning quality due to silent tail-truncation
- Excessive KV-cache memory allocation leading to container Out-Of-Memory (OOM) terminations

This lab implements a deterministic, local **Token Budget Preflight** check that inspects incoming prompt payloads before dispatching them to containerized endpoints, reporting retained tokens, explicit truncation counts, and telemetry flags.

## Contract Specification

1. **Configured Budget**: Non-negative integer representing the maximum allowable token limit. Supplying a negative integer raises a `ValueError`.
2. **Overflow Handling**: Given budget `3` and input `"one two three four"`, the checker retains `['one', 'two', 'three']` (count: 3), reports `1` removed token (`['four']`), and marks `truncated = True`.
3. **Empty Input**: Given empty input `""` or whitespace-only input, the checker retains `[]` (count: 0), reports `0` removed tokens (`[]`), and marks `truncated = False`.
4. **Boundary Matching**: When prompt token count equals the budget limit exactly, all tokens are retained with `0` removed tokens and `truncated = False`.
5. **Preflight Telemetry**: The returned report provides comprehensive fields mapped to cloud deployment concepts (`prompt`, `budget`, `total_tokens`, `total_token_count`, `retained_tokens`, `retained_count`, `removed_tokens`, `removed_count`, `truncated`, and `tokenizer_note`).

## Concept Mapping

| Public Field | Containerized Cloud Deployment Concept |
| :--- | :--- |
| `budget` | Container sequence capacity / memory budget (e.g., vLLM `--max-model-len 4096`) |
| `prompt` | Inbound client query payload submitted to the container HTTP endpoint |
| `total_tokens` | Tokenized representation of user input prior to admission |
| `total_token_count` | Raw token workload before applying admission limits |
| `retained_tokens` | Admitted token slice passed to the container inference engine |
| `retained_count` | Length of token sequence allocated in the model context buffer |
| `removed_tokens` | Dropped tokens preventing container memory exhaustion |
| `removed_count` | Explicit telemetry count of pruned tokens for audit logging |
| `truncated` | Admission boolean flag indicating whether the prompt required truncation |
| `tokenizer_note` | Explicit disclosure of pedagogical approximation vs production BPE tokenizer |

## Scope, Limitations & Simulation Notice

> [!NOTE] Teaching Approximation Notice
> The preflight checker uses deterministic whitespace splitting (`text.strip().split()`) as a pedagogical approximation to demonstrate admission control, token counting, and telemetry.
> 
> In production containerized cloud pipelines, replace this fixture with the specific model's native subword/BPE tokenizer (e.g., Hugging Face `AutoTokenizer` for Phi-4-mini or vLLM's internal tokenizer).
> 
> This lab requires no model download, GPU hardware, Docker daemon, or paid cloud provider credentials. It makes no unsupported claims regarding real hardware latency or trained-model reasoning accuracy.

## File Structure

- `example.py`: Core `TokenBudgetPreflight` class, conceptual mappings, and interactive CLI demo.
- `test_example.py`: Comprehensive test suite verifying normal, boundary, and error scenarios.
- `README.md`: Architectural documentation, contract specification, and test instructions.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module03/applied-labs/r04-t051 -p "test_*.py"
```
