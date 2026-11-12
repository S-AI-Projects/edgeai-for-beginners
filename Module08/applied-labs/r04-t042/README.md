# R04-T042 - Prompt-template escaping: compare two approaches

Companion to [Module08/05.AIPoweredAgents.md](../../05.AIPoweredAgents.md)
("Session 5: Build AI-Powered Agents Fast with Foundry Local").

## What it teaches
A prompt template should declare its variables, reject missing or unknown keys, and keep
user data visibly separate from the fixed instruction text. Braces inside user data must
stay literal. `example.py` compares two ways to do this on identical inputs.

| Approach | What it is | Rejects missing key | Rejects unknown key | Labels data vs instruction |
|---|---|---|---|---|
| A. direct | `PromptTemplate.render()` / `render_parts()` | yes | yes | yes |
| B. reference | Python's `str.format` (simple independent calculation) | yes (raises `KeyError`) | **no** (ignores extras) | no |

| Public part | Meaning in the lesson |
|---|---|
| `PromptTemplate(text, variables)` | declares the variables; the text may only use `{variable}` placeholders |
| `render_parts(values)` | returns `("instruction"\|"data", text)` segments so the boundary is visible |
| `render(values)` | the joined prompt string |
| `TemplateError.code` | `MISSING_KEY`, `UNKNOWN_KEY`, `NON_STRING_VALUE`, `BAD_TEMPLATE` |

## Run
```bash
python3 Module08/applied-labs/r04-t042/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t042 -p "test_*.py"
```
Python 3 standard library only. No model download, paid provider, GPU or device.

## Expected output
```
template: 'Write a short note for {name} about {topic}.'
normal:
  direct    -> OK 'Write a short note for Asha about edge AI.'
  reference -> OK 'Write a short note for Asha about edge AI.'
braces in data:
  direct    -> OK 'Write a short note for Asha about {name} and {topic}.'
  reference -> OK 'Write a short note for Asha about {name} and {topic}.'
missing topic:
  direct    -> REJECTED MISSING_KEY
  reference -> REJECTED KeyError(topic)
unknown key:
  direct    -> REJECTED UNKNOWN_KEY
  reference -> OK 'Write a short note for Asha about edge AI.'
injection-looking text:
  direct    -> OK 'Write a short note for Asha about Ignore previous instructions.'
  reference -> OK 'Write a short note for Asha about Ignore previous instructions.'
note: templating keeps data visible; it does not prevent prompt injection.
```

## Limits (what this is NOT)
- **Templating alone does not prevent prompt injection.** Text such as "Ignore previous
  instructions" is passed through unchanged, and a real model may still follow it. Keeping
  data in a labelled segment only makes the boundary visible and testable.
- This is a simulation of template rendering. It calls no model and makes no claim about
  real hardware, cloud service behaviour or trained-model performance.
