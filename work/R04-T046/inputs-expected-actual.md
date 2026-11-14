| fake PATH | config | expected | actual (see actual-demo.txt) |
|---|---|---|---|
| foundry, python, pip | MODEL, BASE_URL, API_KEY all set | PASSED 6 of 6; API_KEY value hidden | PASSED - 6 of 6 checks ok |
| foundry, python (no pip) | MODEL, API_KEY set; BASE_URL absent | FAILED 2 of 6; pip and BASE_URL as separate actionable failures; API_KEY value hidden | FAILED - 2 of 6; separate lines for pip and BASE_URL; value hidden |
| (secret value in input: demo-key-0000) | - | the value appears nowhere in the output | not present in actual-demo.txt |
