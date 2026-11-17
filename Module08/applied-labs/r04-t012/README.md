# R04-T012 - Prompt Template Escaping: Boundary-Case Lesson Extension

Companion applied lab to [Module08/05.AIPoweredAgents.md](../../05.AIPoweredAgents.md) ("Session 5: Build AI-Powered Agents Fast with Foundry Local - Part 1: System Prompts and Grounding").

---

## 1. How this Illustrates the Lesson, and Where it Stops

### Lesson Context
In agentic architectures built with Foundry Local and Small Language Models, system prompts ground the agent's behavior, roles, and tool contracts. Templating separates fixed developer instructions from variable user data.

This lab demonstrates:
1. **Strict Variable Contracts**: Templates declare exact placeholders (e.g. `{name}`, `{topic}`). All declared placeholders must be supplied; missing variables are rejected (`MISSING_VARIABLE`).
2. **Rejection of Unknown Keys**: Extraneous variables not declared in the template are rejected (`UNKNOWN_VARIABLE`), preventing unintended variable injection.
3. **Literal Preservation of User Data**: Single-pass regex substitution ensures user input containing literal curly braces (such as JSON snippets or formatting tokens like `{admin=True}`) are preserved literally and never re-evaluated as template tags.

### Boundary Decisions & Scope Limitations
* **Boundary Policy**:
  * Missing declared variable: **Strict error** (`MISSING_VARIABLE`), never silently defaulted to empty strings.
  * Extra undeclared keys: **Strict error** (`UNKNOWN_VARIABLE`).
  * Literal braces in user data: **Preserved literally** as plain text.
* **Prompt Injection Disclaimer**:
  > **Important:** While safe template substitution isolates structural syntax (preventing template engine crashes and secondary variable resolution), **templating alone does not prevent prompt injection**. Semantic attacks (e.g. "Ignore previous instructions") must be mitigated through delimiter framing, system prompt constraints, and model guardrails.
* **Prerequisites**: Python 3 standard library only. No model weights, API keys, or GPU hardware required.

---

## 2. Canonical Task Fixture

* **Template**: `"Hello {name}, your assigned topic is {topic}."`
* **Normal Input**: `{"name": "Alice", "topic": "Edge AI"}`
  * **Output**: `"Hello Alice, your assigned topic is Edge AI."`
* **Boundary Input**: `{"name": "Bob {admin=True}", "topic": "SLMs with {nested_tag}"}`
  * **Output**: `"Hello Bob {admin=True}, your assigned topic is SLMs with {nested_tag}."` (braces remain literal).
* **Missing Variable**: `{"name": "Charlie"}` -> Rejection with `MISSING_VARIABLE` (`topic`).

---

## 3. Run and Verify

```bash
python3 Module08/applied-labs/r04-t012/example.py
python3 -m unittest discover -s Module08/applied-labs/r04-t012 -p "test_*.py"
```
Ran 14 tests in ~0.001s, OK.
