# R04-T045 - Capability negotiation: refactor the teaching example

Companion to [Module08/04.CuttingEdgeModels.md](../../04.CuttingEdgeModels.md)
("Session 4: Building Production Chat Applications with Chainlit").

## How this illustrates the lesson, and where it stops
The lesson never uses the term "capability negotiation", but it keeps doing the same thing:
it **discovers what is available and then gates on it**. The Chainlit app asks the Foundry Local
manager for the endpoint and model info (with a manual fallback); the WebGPU demo checks
`'gpu' in navigator` before running; and the routing sketch sends each task type only to a
backend that suits it. `example.py` isolates that idea: two sides declare what they support,
only the **intersection** is allowed, and a request outside it is refused **before** anything is
dispatched.

**Simplifications:** capability names (`tools`, `resources`, `prompts`) are labels from the
task fixture. There is no network, handshake, protocol version or authentication, and nothing
here calls Chainlit, Foundry Local, an OpenAI client or WebGPU.

## The refactor (same contract, one responsibility extracted)
| Version | What it does |
|---|---|
| `invoke_baseline()` | the correct baseline: validate, negotiate, gate and dispatch all inline |
| `invoke_refactored()` | identical behaviour; calls the extracted function below |
| `negotiate_capabilities(client, server)` | **the extracted responsibility**: validate both sets, return the intersection |

Extracting it makes negotiation a pure function that can be tested on its own (commutative,
inputs not modified, result is a subset of both sides) and reused by any caller.

**Before/after equivalence:** `equivalence_report()` runs both versions on the task fixture and on
every combination of the three capability names (all client sets x all server sets x each requested
capability plus an unknown one x two handler setups = 512 cases) and compares both the outcome and
which handlers were actually called. The test suite also checks that this comparison **can fail**
by feeding it a deliberately wrong version.

## Error codes
`NOT_NEGOTIATED` (rejected before dispatch), `NO_HANDLER` (negotiated but nothing registered),
`BAD_CAPABILITY_SET` (not a set/list/tuple of non-empty strings, e.g. a bare string),
`BAD_REQUEST` (requested capability is not a non-empty string).

## Run
```bash
python3 Module08/applied-labs/r04-t045/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t045 -p "test_*.py"
```
Python 3 standard library only. No model download, paid provider, GPU or device.

## Expected output
```
client capabilities: ['resources', 'tools']
server capabilities: ['prompts', 'tools']
negotiated: ['tools']
  invoke tools: OK 'tools-handled:ping' (handler calls: ['tools'])
  invoke resources: REJECTED NOT_NEGOTIATED (handler calls: [])
  invoke prompts: REJECTED NOT_NEGOTIATED (handler calls: [])
baseline vs refactored on the fixture: identical outcomes
baseline vs refactored on all 512 generated cases: 0 mismatches
note: capability names are labels; this is a simulation, not a real client/server.
```

## Limits
This is a simulation of capability intersection and gating on hand-written sets. It makes no claim
about real hardware, cloud service behaviour, or what any real client or server supports.
