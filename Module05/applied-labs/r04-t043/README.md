# R04-T043 - Teacher/student probability comparison: invariant and state trace

Companion to [Module05/02.SLMOps-Distillation.md](../../02.SLMOps-Distillation.md)
("Section 2: Model Distillation - From Theory to Practice").

## How this illustrates the lesson, and where it stops
The lesson describes training a student to minimise the difference from the teacher's
outputs, and mentions adjusting teacher output softness. `example.py` shows the smallest
version of that idea: comparing a teacher probability distribution with a student one using
**cross-entropy**, \sum_i p_i \ln(\max(q_i, \text{floor}))$.
It makes two practical points visible: both distributions must be valid and normalised
before they are compared, and a small positive **floor** inside the log stops a student
probability of 0 from producing an infinite loss.

**Simplifications:** the probabilities are typed in by hand. There is no model, softmax,
temperature, batch, training loop or optimiser here, and the lesson's case-study numbers
are not used or checked.

## The invariant and the state trace
The calculation records its state after every step: the class index, p, q, the floored q,
the term and the running total. `check_invariant()` then verifies the link between that
state and the final output:
1. every term is >= 0
2. each running total equals the sum of the terms so far
3. running totals never decrease
4. the final result equals the last running total

| Public part | Meaning |
|---|---|
| `cross_entropy(teacher, student, floor=1e-12)` | the final number |
| `cross_entropy_trace(...)` | the same calculation, returning every step's state |
| `check_invariant(trace)` | list of violations (empty means consistent) |
| `DistributionError.code` | `EMPTY`, `NON_NUMERIC`, `NOT_FINITE`, `NEGATIVE_PROBABILITY`, `NOT_NORMALIZED`, `LENGTH_MISMATCH`, `BAD_FLOOR` |

## Run
```bash
python3 Module05/applied-labs/r04-t043/example.py
python3 -m unittest discover -s Module05/applied-labs/r04-t043 -p "test_*.py"
```
Python 3 standard library only. No model download, paid provider, GPU or device.

## Expected output
```
floor = 1e-12   (ln(2) = 0.693147)
teacher [1,0] vs student [0.5,0.5]:
  step 0: p=1.0000 q=0.5000 q_floored=5.0e-01 term=0.693147 running=0.693147
  step 1: p=0.0000 q=0.5000 q_floored=5.0e-01 term=0.000000 running=0.693147
  result=0.693147  invariant holds
identical one-hot [1,0]:
  step 0: p=1.0000 q=1.0000 q_floored=1.0e+00 term=0.000000 running=0.000000
  step 1: p=0.0000 q=0.0000 q_floored=1.0e-12 term=0.000000 running=0.000000
  result=0.000000  invariant holds
floor in action: teacher [1,0] vs student [0,1]:
  step 0: p=1.0000 q=0.0000 q_floored=1.0e-12 term=27.631021 running=27.631021
  step 1: p=0.0000 q=1.0000 q_floored=1.0e+00 term=0.000000 running=27.631021
  result=27.631021  invariant holds
teacher not normalized:
  REJECTED NOT_NORMALIZED
length mismatch:
  REJECTED LENGTH_MISMATCH
negative probability:
  REJECTED NEGATIVE_PROBABILITY
note: probabilities are typed in by hand; this is a simulation, not a trained model.
```

## Limits (what this is NOT)
This is a simulation of one loss calculation on hand-written numbers. It makes no claim
about real hardware, cloud service behaviour, or how well any trained or distilled model
performs.
