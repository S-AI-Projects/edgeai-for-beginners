| scenario | fixture | expected exit | actual exit | expected text found | match |
|---|---|---|---|---|---|
| normal: matching OS/arch/backend | ok_macos14_arm_mlx.json | 0 | 0 | yes | yes |
| boundary: exact minimums | ok_boundary_minimums.json | 0 | 0 | yes | yes |
| failure: changed architecture | rosetta_architecture_i386.json | 1 | 1 | yes | yes |
| failure: missing capability | missing_backend.json | 2 | 2 | yes | yes |
| failure: invalid data | invalid_ram_gb.json | 3 | 3 | yes | yes |
