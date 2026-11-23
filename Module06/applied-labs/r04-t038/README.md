# R04-T038: Bounded Conversation Memory Evaluation Experiment

## Overview
This lab extends `Module06/03.IntroduceMCP.md` by demonstrating a bounded conversation memory buffer that limits context size while preserving defensive caller isolation.

### Contracts & Behaviors
1. **FIFO Bounded Retention**:
   - Buffer capacity $K = 3$.
   - Adding records $[A, B, C, D]$ drops $A$ and retains $[B, C, D]$ in arrival order.
2. **Defensive Isolation**:
   - `get_records()` returns a deep copy. In-place modification, deletion, or appendage by callers does not affect internal stored memory.
3. **Controlled Capacity Evaluation Experiment**:
   - Evaluates three configurations: $K \in \{2, 3, 5\}$ across a 6-record input stream.
   - Measures retention ratio and eviction counts:
     - $K=2$: 2 retained, 4 evicted (Retention 33.3%)
     - $K=3$: 3 retained, 3 evicted (Retention 50.0%)
     - $K=5$: 5 retained, 1 evicted (Retention 83.3%)
   - Shows trade-off: higher memory bounds preserve more recent turn context at the cost of larger prompt token counts.

## Execution
```bash
python3 Module06/applied-labs/r04-t038/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module06/applied-labs/r04-t038 -p "test_*.py"
```
