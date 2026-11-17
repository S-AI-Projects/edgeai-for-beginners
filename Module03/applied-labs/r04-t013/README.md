# R04-T013 - Token-Budget Preflight: Compare Two Approaches

Companion applied lab to [Module03/03.DeployingSLMinCloud.md](../../03.DeployingSLMinCloud.md) ("Containerized Cloud Deployment - Production-Scale Solutions: Introduction to Phi-4-mini Container Deployment").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
Deploying Small Language Models (such as Phi-4-mini-instruct) in containerized cloud runtimes (vLLM, Ollama, ONNX Runtime) requires deterministic request admission control. Serving engines operate within fixed context length limits and GPU/CPU KV cache budgets. A token-budget preflight inspects input prompt lengths before invoking containerized endpoints, trimming over-budget prompts and recording token counts.

This lab demonstrates:
1. **Deterministic Truncation**: Enforcing a configured token budget against input text.
2. **Explicit Accounting**: Reporting total tokens, retained tokens, and exact count of removed tokens.
3. **Budget Validation**: Rejecting negative budgets (`INVALID_BUDGET`) and invalid prompt structures.
4. **Comparison of Two Approaches**:
   * **Direct Implementation**: Slices token sequences up to the budget.
   * **Independent Calculation**: Uses bounded arithmetic (`min(total, budget)` and `max(0, total - budget)`) to independently compute retained and removed counts. Both approaches are verified for mathematical equivalence.

### Scope and Limitations
* **Teaching Approximation Disclaimer**:
  > **Note:** The tokenizer implemented here is a deterministic whitespace-based tokenizer designed for pedagogical clarity. It is **not** a subword BPE or WordPiece tokenizer (such as Phi-4's 200K TikToken/SentencePiece vocabulary). In production, replace `tokenize_approx` with your engine's target tokenizer.
* **Prerequisites**: Python 3 standard library only. No model weights, GPU runtime, or container daemon required.

---

## 2. Canonical Task Fixture

* **Input Prompt**: `"one two three four"`
* **Configured Budget**: `3`
* **Direct & Independent Results**:
  * Total tokens: `4`
  * Retained tokens: `["one", "two", "three"]`
  * Removed count: `1`
  * Truncated: `True`
* **Boundary Behaviors**:
  * Empty prompt `""` with budget `3` $\rightarrow$ retained `[]`, removed `0`.
  * Negative budget `-1` $\rightarrow$ rejected with `INVALID_BUDGET`.

---

## 3. Run and Verify

```bash
python3 Module03/applied-labs/r04-t013/example.py
python3 -m unittest discover -s Module03/applied-labs/r04-t013 -p "test_*.py"
```
Ran 12 tests in ~0.001s, OK.
