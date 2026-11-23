# R04-T036: Model-Manifest Selection (Failure and Recovery Example)

## Overview
This lab extends `Module08/03.OpenSourceModels.md` by demonstrating resilient manifest parsing, structured error generation for malformed/missing metadata, and clean recovery on subsequent valid inputs.

### Core Behaviors
- **Manifest Validation**: Validates presence of `id`, `required_ram_gb`, and `max_context`. Missing or malformed data reports structured `MALFORMED_MANIFEST_ENTRY` diagnostics without unhandled exceptions.
- **Clean Recovery**: State is not corrupted across evaluation calls; a subsequent valid manifest executes normally.
- **Teaching Fixtures**:
  - Fixture A: RAM 4GB, Context 2048
  - Fixture B: RAM 8GB, Context 4096
  - Budget: RAM 6GB, Requested Context 1024 -> Admits only Fixture A.

## Execution
```bash
python3 Module08/applied-labs/r04-t036/example.py
```

## Running Unit Tests
```bash
python3 -m unittest discover -s Module08/applied-labs/r04-t036 -p "test_*.py"
```
