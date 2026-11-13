| plan (stage: reads -> writes) | expected | actual (see actual-demo.txt) |
|---|---|---|
| export: source_model -> ov_ir; quantize: ov_ir -> ov_int8; benchmark: ov_int8 -> bench_report | accepted, run through the adapter in that order | accepted, adapter calls [export, quantize, benchmark] |
| export; benchmark; quantize | rejected OUT_OF_ORDER, adapter never called | rejected OUT_OF_ORDER (adapter calls: 0) |
| export; quantize reading ov_int8_typo | rejected UNKNOWN_ARTIFACT, adapter never called | rejected UNKNOWN_ARTIFACT (adapter calls: 0) |
| good plan, adapter fails at quantize | ADAPTER_FAILED, benchmark never runs | ADAPTER_FAILED, completed ['export'] |
