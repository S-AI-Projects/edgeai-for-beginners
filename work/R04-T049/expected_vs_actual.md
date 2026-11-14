| scenario | fixture | expected exit | actual exit | expected text found | match |
|---|---|---|---|---|---|
| normal: matching OS/arch/backend | ok_windows11_npu.json | 0 | 0 | yes | yes |
| normal: second listed backend | ok_directml_backend.json | 0 | 0 | yes | yes |
| boundary: nothing reported | empty_fixture.json | 2 | 2 | yes | yes |
| failure: changed architecture | cpu_architecture.json | 1 | 1 | yes | yes |
| failure: wrong OS | wrong_os.json | 1 | 1 | yes | yes |
| failure: missing backend | missing_backend.json | 2 | 2 | yes | yes |
| failure: invalid data | invalid_sdk_flag.json | 3 | 3 | yes | yes |
