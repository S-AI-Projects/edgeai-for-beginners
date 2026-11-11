# Applied Lab R04-T003: Installation Preflight Report — Approach Comparison

## Overview

Deploying Microsoft Foundry Local in edge setups requires preflight verification of required system binaries (such as `foundry`, `python3`) and configuration items (such as `model_dir`, `endpoint`, and API tokens). 

This lab implements a strictly read-only, non-network preflight checker that:
1. Distinguishes missing executable binaries from absent configuration parameters with separate actionable messages.
2. Sanitizes sensitive values (e.g., API keys, passwords, bearer tokens) so secrets are never printed to terminal or log files.
3. Compares the direct object-oriented verification approach against a declarative set-based reference evaluator over identical inputs.

## Comparison of Two Approaches

- **Approach 1 (Direct Procedural Check)**: The `InstallationPreflightChecker` evaluates binaries and config sequentially, classifying errors into `executable_failures` and `config_failures`.
- **Approach 2 (Declarative Reference Evaluator)**: The `reference_preflight_evaluator` computes missing dependencies via set difference and applies dictionary comprehension for key masking.

Both approaches yield identical results for validation status, failure messages, and sanitized diagnostics.

## Scope & Limitations

> [!NOTE] Offline Simulation
> This preflight check operates strictly locally on mock dictionaries/fixtures without installing packages or issuing outbound network calls. Real service connectivity and model execution require the Foundry Local service to be running locally.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module08/applied-labs/r04-t003 -p "test_*.py"
```
