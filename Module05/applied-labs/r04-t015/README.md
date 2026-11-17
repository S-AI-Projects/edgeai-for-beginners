# R04-T015 - Teacher/Student Probability Comparison: Offline Service Adapter

Companion applied lab to [Module05/02.SLMOps-Distillation.md](../../02.SLMOps-Distillation.md) ("Section 2: Model Distillation - From Theory to Practice: Stage 2: Student Model Fine-tuning").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
In Small Language Model distillation, knowledge is transferred from a large teacher LLM to a compact student SLM by matching their output probability distributions. The fine-tuning objective minimizes the cross-entropy loss between the teacher's target distribution and the student's predicted logits:
$$H(P, Q) = - \sum_{i} P_i \ln(Q_i)$$

This lab demonstrates:
1. **Distribution Validation**: Confirms probabilities are non-negative, dimension-matched, and sum to 1.0.
2. **Log Floor Stability**: Applies a small positive floor ($\epsilon = 10^{-12}$) to prevent numerical instability ($\ln(0)$).
3. **Canonical Behaviors**:
   * Teacher $[1, 0]$ vs Student $[0.5, 0.5]$ yields $\ln(2) \approx 0.693147$.
   * Identical one-hot distributions $[1, 0]$ vs $[1, 0]$ approach $0.0$.
4. **Offline Adapter Interface**: Places external prediction services behind a `ProbabilityProvider` interface and supplies a deterministic `LocalDistillationAdapter`.

### Scope and Limitations
* **Local Mock Boundaries**: The offline adapter isolates mathematical loss computation. It **does not** establish real GPU backpropagation passes, temperature scaling ($\tau$), gradient accumulation, or non-deterministic FP16 tensor precision.
* **Prerequisites**: Python 3 standard library only.

---

## 2. Canonical Task Fixture

* **Soft Target Case**:
  * Teacher: `[1.0, 0.0]`
  * Student: `[0.5, 0.5]`
  * Cross-Entropy: $\ln(2) \approx 0.693147$
* **Identical Target Case**:
  * Teacher: `[1.0, 0.0]`
  * Student: `[1.0, 0.0]`
  * Cross-Entropy: `0.0` (approaches zero with epsilon floor)

---

## 3. Run and Verify

```bash
python3 Module05/applied-labs/r04-t015/example.py
python3 -m unittest discover -s Module05/applied-labs/r04-t015 -p "test_*.py"
```
Ran 14 tests in ~0.001s, OK.
