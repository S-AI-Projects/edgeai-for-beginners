Evidence for R04-T043 (do NOT include work/ in any upstream PR).
- inputs-expected-actual.md: inputs with expected vs actual results
- actual-normal.txt: 26 tests, OK, exit=0
- actual-demo.txt: demo output with the recorded state after each step (matches README / lesson)
- actual-mutation.txt: ln replaced by log2 on purpose -> tests FAIL, exit=1 (a wrong result is caught)
- tool-versions.txt
