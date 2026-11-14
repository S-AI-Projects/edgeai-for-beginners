| scenario | fixture | expected exit | actual exit | expected text found | match |
|---|---|---|---|---|---|
| normal: matching OS/arch/backend | ok_linux_x86_64_htp.json | 0 | 0 | yes | yes |
| normal: android target with NDK | ok_android_with_ndk.json | 0 | 0 | yes | yes |
| boundary: python exactly 3.7 | boundary_python_3_7.json | 0 | 0 | yes | yes |
| boundary: NDK not needed off-android | ndk_not_needed.json | 0 | 0 | yes | yes |
| failure: changed architecture | armv7_android_target.json | 1 | 1 | yes | yes |
| failure: missing backend | missing_backend.json | 2 | 2 | yes | yes |
| failure: missing NDK on android target | missing_android_ndk.json | 2 | 2 | yes | yes |
| failure: invalid data | invalid_sdk_flag.json | 3 | 3 | yes | yes |
