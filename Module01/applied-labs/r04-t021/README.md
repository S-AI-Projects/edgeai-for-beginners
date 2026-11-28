# R04-T021: Token-Budget Preflight Example

A deterministic, local whitespace-token preflight check demonstrating how incoming prompts are evaluated against a configured token budget before inference on resource-constrained edge devices.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module01/01.EdgeAIFundamentals.md`:** Edge devices operate under strict memory and compute limits. Running a preflight check before local SLM inference prevents unbounded prompts from exhausting edge device RAM or exceeding context limits, and makes truncation visible to the caller.
- **Where simplifications stop:** `prompt.split()` is a deterministic teaching approximation only. It does **not** model real subword tokenizers (BPE, WordPiece, SentencePiece), byte/KV-cache RAM allocation, thermal throttling, latency, or model accuracy.

## Public Input / Output Mapping to Lesson Concepts

| Symbol | Role | Lesson Concept |
|---|---|---|
| `prompt` (`str`) | Incoming text before local inference | Local user/sensor input evaluated on-device |
| `budget` (`int >= 0`) | Configured maximum allowed token count | Edge device context/memory resource limit |
| `retained_tokens` (`list[str]`) | Prefix of tokens fitting within `budget` | Bounded payload admitted for on-device inference |
| `retained_count` (`int`) | Number of retained tokens | Consumed resource budget |
| `removed_count` (`int`) | Count of dropped trailing tokens | Truncation loss caused by edge resource limits |
| `truncated` (`bool`) | Whether `removed_count > 0` | Preflight signal for caller fallback or warning |
| `tokenizer_note` (`str`) | Explicit approximation disclaimer | Distinguishes teaching fixture from real model tokenizers |

## Files
- `example.py` — Implements `check_token_budget(prompt, budget)` using whitespace splitting.
- `test_example.py` — Unit tests covering normal, boundary, empty-input, and negative-budget scenarios.

## Prerequisites
- Python 3 standard library only (no external packages, model downloads, or GPU required).

## Usage & Verification

- **Run the standalone concept example:**
  `python3 Module01/applied-labs/r04-t021/example.py`

- **Run the automated test suite:**
  `python3 -m unittest discover -s Module01/applied-labs/r04-t021 -p "test_*.py"`

## Scope & Limitations
- **Teaching Approximation:** Uses `prompt.split()` (whitespace tokenization) solely as a deterministic teaching approximation, **not** a real model tokenizer (such as BPE or WordPiece).
- **No Hardware/Model Claims:** Makes no claims regarding real edge device latency, memory usage, or trained model accuracy.
