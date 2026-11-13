# Applied Lab R04-T052: Bounded Conversation Memory — MCP Integration

## Overview

In Model Context Protocol (MCP) host-client architectures, an AI assistant coordinates with MCP tools, data resources, and user prompts across multi-turn sessions. On edge devices hosting Small Language Models (SLMs) such as Microsoft Phi-4-mini, memory and context windows are strictly constrained.

If conversation history grows unbounded:
- The SLM context buffer is rapidly saturated, degrading inference quality and prompting OOM errors.
- Shared references between MCP tool callers and internal buffers risk uncontrolled state mutation.

This lab implements a deterministic, local **Bounded Conversation Memory** fixture that stores at most three conversation records in arrival order and exposes isolated defensive copies to callers.

## Contract Specification

1. **Capacity Limit**: Buffer retains at most 3 conversation records in arrival order (oldest to newest).
2. **FIFO Eviction on Overflow**: Adding records `['A', 'B', 'C', 'D']` retains `['B', 'C', 'D']`, evicting `'A'`.
3. **Defensive Copying**: `get_records()` returns an isolated deep copy; mutating the returned list or its contents (e.g. `append`, `pop`, `clear`, or in-place item reassignment) has **zero** effect on internal memory.
4. **Smallest Valid Cases**:
   - Empty memory: `len == 0`, `get_records() == []`.
   - Single item addition: adding `'A'` yields `['A']`.
   - Smallest valid capacity: capacity of `1` retains only the single most recent record.
5. **Boundary Cases**:
   - Exact capacity match: adding 3 records (`A`, `B`, `C`) fills the buffer with `evicted = None` and `truncated = False`.
   - First overflow: adding the 4th record (`D`) triggers eviction of `A`.
   - Continuous overflow: adding `E` evicts `B`, retaining `['C', 'D', 'E']`.
6. **Invalid Cases**:
   - Initializing with capacity `< 1` raises `ValueError`.
   - Adding `None` or empty whitespace strings raises `ValueError`.

## Boundary Decision Matrix

| Scenario | Input Action | Internal State Before | Evicted Record | Internal State After | Truncated Flag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Empty State** | None (init) | `[]` | None | `[]` | `False` |
| **Single Entry** | `add("A")` | `[]` | None | `['A']` | `False` |
| **Under Capacity** | `add("B")` | `['A']` | None | `['A', 'B']` | `False` |
| **Exact Boundary** | `add("C")` | `['A', 'B']` | None | `['A', 'B', 'C']` | `False` |
| **First Overflow** | `add("D")` | `['A', 'B', 'C']` | `'A'` | `['B', 'C', 'D']` | `True` |
| **Second Overflow**| `add("E")` | `['B', 'C', 'D']` | `'B'` | `['C', 'D', 'E']` | `True` |
| **Invalid Capacity** | `init(capacity=0)` | N/A | N/A | Raises `ValueError` | N/A |
| **Invalid Record** | `add(None)` | `['C', 'D', 'E']` | None | Raises `ValueError` | N/A |

## Concept Mapping to MCP Integration

| Component | MCP Architecture Concept (Module 06) |
| :--- | :--- |
| `capacity = 3` | Context window turn ceiling preventing SLM context exhaustion in MCP sessions |
| `add_record()` | Inbound admission of user turns, assistant reasoning, and MCP tool call responses |
| `evicted` | Oldest conversational turn pruned under FIFO retention policy |
| `get_records()` | Isolated context history supplied to MCP prompts/tools without mutation risk |
| `FIFO Sliding Window`| Predictable $O(1)$ memory bound ensuring reliable multi-turn edge assistant operation |

## Scope, Limitations & Simulation Notice

> [!NOTE] Teaching Approximation & Simulation Notice
> This fixture illustrates in-memory buffer sizing and defensive copying semantics for MCP session context.
> 
> In a production MCP deployment, context buffering may incorporate subword token counting (e.g. via TikToken or Hugging Face tokenizers) and persistent persistence adapters (e.g. SQLite or Redis).
> 
> This is a minimal local verification fixture: no model download, GPU hardware, Docker daemon, or paid cloud service is required. The example makes no unsupported claims regarding real hardware latency or trained-model inference capabilities.

## File Structure

- `example.py`: Core `BoundedConversationMemory` class, boundary decisions, and interactive CLI demo.
- `test_example.py`: 12 automated unit tests verifying normal, boundary, immutability, and error handling scenarios.
- `README.md`: Technical documentation, contract specification, and boundary decision matrix.

## Verification & Execution

### Run CLI Demonstration
```bash
python3 example.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s Module06/applied-labs/r04-t052 -p "test_*.py"
```
