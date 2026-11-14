| client | server | invoke | expected | actual (see actual-demo.txt) |
|---|---|---|---|---|
| {tools, resources} | {tools, prompts} | (negotiate) | {tools} | ['tools'] |
| {tools, resources} | {tools, prompts} | tools | handled, handler called once | OK 'tools-handled:ping', calls ['tools'] |
| {tools, resources} | {tools, prompts} | resources | rejected NOT_NEGOTIATED before dispatch | REJECTED NOT_NEGOTIATED, calls [] |
| {tools, resources} | {tools, prompts} | prompts | rejected NOT_NEGOTIATED before dispatch | REJECTED NOT_NEGOTIATED, calls [] |
| baseline vs refactored | all 512 generated cases | - | identical outcome and handler calls | 0 mismatches |
