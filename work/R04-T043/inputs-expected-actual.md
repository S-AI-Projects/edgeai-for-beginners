| teacher | student | expected | actual (see actual-demo.txt) |
|---|---|---|---|
| [1, 0] | [0.5, 0.5] | ln(2) = 0.693147 | 0.693147 |
| [1, 0] | [1, 0] | 0 | 0.000000 |
| [1, 0] | [0, 1] | -ln(1e-12) = 27.631021 (floor, not infinity) | 27.631021 |
| [0.5, 0.4] | [0.5, 0.5] | rejected NOT_NORMALIZED | rejected NOT_NORMALIZED |
| [1, 0] | [1] | rejected LENGTH_MISMATCH | rejected LENGTH_MISMATCH |
| [1.5, -0.5] | [0.5, 0.5] | rejected NEGATIVE_PROBABILITY | rejected NEGATIVE_PROBABILITY |
