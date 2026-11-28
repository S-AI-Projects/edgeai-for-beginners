# R04-T030: Token-Budget Preflight — Scenario Assessment

A deterministic local whitespace-token preflight check paired with three applied scenario-assessment questions (predict output, diagnose failure, choose boundary policy), each backed by a rationale and executable check.

## Lesson Connection & Simplification Boundary
- **How it illustrates `Module03/01.SLMAdvancedLearning.md`:** Deploying SLMs under strict memory and context limits requires preflight checks that bound prompt length and report truncation before inference starts.
- **Where simplifications stop:** `prompt.split()` is a teaching approximation, **not** the model's real subword tokenizer (BPE/WordPiece/SentencePiece). It makes no claims about real hardware, quantization footprints, cloud services, or trained-model performance.

## Applied Scenario Questions, Rationales & Executable Checks

1. **Q1 — Predict an output:** What does `check_token_budget("one two three four", budget=3)` return?
   - **Answer:** `retained_tokens=['one', 'two', 'three']`, `retained_count=3`, `removed_count=1`, `truncated=True`.
   - **Rationale:** Whitespace splitting yields 4 tokens; slicing `tokens[:3]` retains the first 3 tokens and removes the 4th.
   - **Executable check:** `verify_q1_predict_output()` in `example.py` (`test_q1_predict_output_budget_3_four_tokens`).

2. **Q2 — Diagnose a failure:** Why does `check_token_budget("alpha beta", budget=-2)` raise `ValueError` instead of returning truncated tokens?
   - **Answer:** Negative budgets are invalid resource limits and must fail fast before tokenization.
   - **Rationale:** Without a `budget < 0` guard, Python slicing `tokens[:-2]` would silently drop trailing tokens or return `[]` without signaling an invalid configuration.
   - **Executable check:** `verify_q2_diagnose_failure()` in `example.py` (`test_q2_diagnose_failure_negative_budget`).

3. **Q3 — Choose a boundary policy:** How should `len(tokens) == budget` and `budget == 0` be handled?
   - **Answer:** Treat `len(tokens) <= budget` as non-truncated (`removed_count=0`, `truncated=False`), and allow `budget=0` as a valid boundary that retains `[]` and reports `removed_count=len(tokens)`.
   - **Rationale:** An exact-fit prompt uses the full budget without loss, whereas `budget=0` deterministically blocks all tokens when a zero-token cap is configured.
   - **Executable check:** `verify_q3_boundary_policy()` in `example.py` (`test_q3_choose_boundary_policy_exact_and_zero`).

## Files
- `example.py` — `check_token_budget` and executable checks `verify_q1_predict_output`, `verify_q2_diagnose_failure`, `verify_q3_boundary_policy`.
- `test_example.py` — Unit tests covering all three questions, empty input, and invalid types.

## Prerequisites
- Python 3 standard library only (no model downloads, GPU, or external services).

## Usage & Verification
```bash
python3 Module03/applied-labs/r04-t030/example.py
python3 -m unittest discover -s Module03/applied-labs/r04-t030 -p "test_*.py"
```
