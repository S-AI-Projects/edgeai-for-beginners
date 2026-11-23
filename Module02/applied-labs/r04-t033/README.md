# R04-T033: Model-Manifest Selection (Invariant and State Trace)

## Overview
This lab extends `Module02/05.mumodel.md` by demonstrating model manifest filtering based on local hardware constraints (available RAM) and task requirements (requested context window length).

### Core Invariants & State Tracing
- **RAM Constraint**: $RAM_{req} \le RAM_{avail}$
- **Context Constraint**: $Context_{max} \ge Context_{req}$
- **Eligibility Invariant**: $Eligible \iff (RAM_{req} \le RAM_{avail}) \land (Context_{max} \ge Context_{req})$
- **State Trace**: Records explicit boolean evaluations and exclusion diagnostics for each candidate model entry.
- **Teaching Fixtures**:
  - Fixture A: RAM 4GB, Context 2048
  - Fixture B: RAM 8GB, Context 4096
  - Budget: RAM 6GB, Requested Context 1024 -> Admits only Fixture A.

*Note: These are synthetic teaching fixtures and do not represent claims about actual physical hardware or production model weights.*

## Execution
```bash
python3 Module02/applied-labs/r04-t033/example.py
```

## Running Tests
```bash
python3 -m unittest discover -s Module02/applied-labs/r04-t033 -p "test_*.py"
```
