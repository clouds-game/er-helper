#!/bin/env bash

workspace_dir=$(dirname $(dirname $(realpath $0)))
echo "Workspace directory: $workspace_dir"
cd "$workspace_dir/vendor/oodle-wrapper"

PATCH1=$(cat <<EOF
diff --git a/test/test.cpp b/test/test.cpp
index 87d32e1..076b364 100644
--- a/test/test.cpp
+++ b/test/test.cpp
@@ -3,6 +3,7 @@
 #include <iostream>
 #include <string.h>
 #include <dlfcn.h>
+#include <cstdint>
 #include <pthread.h>

 typedef size_t(*tDecompressFunc)(uint8_t* srcBuf, size_t srcLen, uint8_t* dstBuf, size_t dstLen, int64_t unk1, int64_t unk2, int64_t unk3, int64_t unk4, int64_t unk5, int64_t unk6, int64_t unk7, int64_t unk8, int64_t unk9, int64_t unk10);
diff --git a/windows_library.cpp b/windows_library.cpp
index 5d08d42..9c65778 100644
--- a/windows_library.cpp
+++ b/windows_library.cpp
@@ -7,6 +7,7 @@
 #include <pe-parse/parse.h>
 #include <sys/mman.h>
 #include <unistd.h>
+#include <utility>

 MappedMemory::MappedMemory(void* mapping, size_t size) :
     m_mapping(mapping),
EOF
)

PATCH2=$(cat <<EOF
diff --git a/linoodle.cpp b/linoodle.cpp
index 059bdf1..5d580ef 100644
--- a/linoodle.cpp
+++ b/linoodle.cpp
@@ -1,44 +1,23 @@

 #include "windows_library.h"

-typedef __attribute__((ms_abi)) size_t(*tDecompressFunc)(uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, size_t dstLen, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t * dstBase, size_t e, void * cb, void * cbCtx, void * scratch, size_t scratchSize, int64_t threadPhase);
-
-typedef __attribute__((ms_abi)) size_t(*tCompressFunc)(int64_t codec, uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, int64_t level, void * opts, size_t offs, size_t unused, void * scratch, size_t scratchSize);
+___TYPEDEF___;

 class OodleWrapper {
 public:
     OodleWrapper() :
         m_oodleLib(WindowsLibrary::Load("oo2core_8_win64.dll"))
     {
-        m_decompressFunc = reinterpret_cast<tDecompressFunc>(m_oodleLib.GetExport("OodleLZ_Decompress"));
-        m_compressFunc = reinterpret_cast<tCompressFunc>(m_oodleLib.GetExport("OodleLZ_Compress"));
+        ___MEMBER_INIT___;
     }

-    size_t Decompress(uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, size_t dstLen, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t * dstBase, size_t e, void * cb, void * cbCtx, void * scratch, size_t scratchSize, int64_t threadPhase)
-    {
-        WindowsLibrary::SetupCall();
-        return m_decompressFunc(srcBuf, srcLen, dstBuf, dstLen, fuzz, crc, verbose, dstBase, e, cb, cbCtx, scratch, scratchSize, threadPhase);
-    }
-    size_t Compress(int64_t codec, uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, int64_t level, void * opts, size_t offs, size_t unused, void * scratch, size_t scratchSize)
-    {
-        WindowsLibrary::SetupCall();
-        return m_compressFunc(codec, srcBuf, srcLen, dstBuf, level, opts, offs, unused, scratch, scratchSize);
-    }
+    ___MEMBER_METHODS___;

 private:
     WindowsLibrary m_oodleLib;
-    tDecompressFunc m_decompressFunc;
-    tCompressFunc m_compressFunc;
+    ___MEMBER_DECLS___;
 };

 OodleWrapper g_oodleWrapper;

-extern "C" size_t OodleLZ_Decompress(uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, size_t dstLen, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t * dstBase, size_t e, void * cb, void * cbCtx, void * scratch, size_t scratchSize, int64_t threadPhase)
-{
-    return g_oodleWrapper.Decompress(srcBuf, srcLen, dstBuf, dstLen, fuzz, crc, verbose, dstBase, e, cb, cbCtx, scratch, scratchSize, threadPhase);
-}
-
-extern "C" size_t OodleLZ_Compress(int64_t codec, uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, int64_t level, void * opts, size_t offs, size_t unused, void * scratch, size_t scratchSize)
-{
-    return g_oodleWrapper.Compress(codec, srcBuf, srcLen, dstBuf, level, opts, offs, unused, scratch, scratchSize);
-}
+___EXTERN_FUNCS___;
EOF
)


# git checkout . --recurse-submodules

# Apply patches
# # git diff --submodule=diff
git checkout .
git -C pe-parse checkout v2.1.1
echo "$PATCH1" | patch -Ntp1
echo "$PATCH2" | patch -Ntp1

# Add more methods
# oo2core_6_win64.dll
OODLE_26_API=$(cat <<EOF
# oo2core_6_win64.dll
extern "C" size_t OodleLZ_Decompress(uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, size_t dst_len, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t* dec_buf_base, size_t dec_buf_size, void* cb, void* cb_ctx, void* scratch, size_t scratch_size, int64_t thread_phase)
extern "C" size_t OodleLZ_Compress(int64_t codec, uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, int64_t level, void* opts, void* dictionary_base, void* lrm, void* scratch, size_t scratch_size)
extern "C" void* OodleLZ_CompressOptions_GetDefault(int64_t codec, int64_t level)
extern "C" size_t OodleLZ_GetCompressedBufferSizeNeeded(size_t src_len)
extern "C" size_t OodleLZ_GetDecodeBufferSize(size_t src_len, bool corruption_possible)
EOF
)

# oo2core_8_win64.dll
OODLE_28_API=$(cat <<EOF
# oo2core_8_win64.dll
extern "C" size_t OodleLZ_Decompress(uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, size_t dst_len, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t* dec_buf_base, size_t dec_buf_size, void* cb, void* cb_ctx, void* scratch, size_t scratch_size, int64_t thread_phase)
extern "C" size_t OodleLZ_Compress(int64_t codec, uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, int64_t level, void* opts, void* dictionary_base, void* lrm, void* scratch, size_t scratch_size)
extern "C" void* OodleLZ_CompressOptions_GetDefault()
extern "C" size_t OodleLZ_GetCompressedBufferSizeNeeded(byte unk, size_t src_len)
extern "C" size_t OodleLZ_GetDecodeBufferSize(byte unk, size_t src_len, bool corruption_possible)
EOF
)

# echo "$OODLE_26_API" | sd 'extern "C" (?P<return>\w+\**) (?P<fn_name>\w+)\((?P<rest>((?P<arg_ty>\w+\**) (?P<arg_name>\w+), )*(?P<last_arg>.*))\)' '{"fn_name": "$fn_name", "return": "$return", "params": "$rest"} <<$arg_name: $arg_ty ++ $last_arg>>'

# output: typedef __attribute__((ms_abi)) size_t(*tDecompressFunc)(uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, size_t dstLen, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t * dstBase, size_t e, void * cb, void * cbCtx, void * scratch, size_t scratchSize, int64_t threadPhase);
TMP=$(echo "$OODLE_26_API" | python -c "$(cat<<EOF
import sys, re
api_version = sys.stdin.readline().strip('#').strip().removesuffix('.dll')
#print("#define OODLE_API_VERSION", api_version)
for line in sys.stdin.readlines():
  capture = re.match(r'extern "C" (?P<return>\w+\**) (?P<fn_name>\w+)\((?P<rest>.*)\)', line).groupdict()
  args = [tuple(s.strip().rsplit(' ', 1)) for s in capture['rest'].split(',')]
  base_name = capture['fn_name'].removeprefix('OodleLZ_')
  capture |= dict(
    api_version = api_version,
    rest_name = ", ".join(b for _, b in args),
    base_name = base_name,
    t_name = f"t{base_name}",
    m_name = f"m_{base_name}",
  )
  print("""
typedef __attribute__((ms_abi)) {return}(*{t_name})({rest});

        {m_name} = reinterpret_cast<{t_name}>(m_oodleLib.GetExport("{fn_name}"));

    {return} {base_name}({rest}) {{
        WindowsLibrary::SetupCall();
        return {m_name}({rest_name});
    }}

    {t_name} {m_name}; // for {api_version}::{fn_name}

extern "C" {return} {fn_name}({rest}) {{
    return g_oodleWrapper.{base_name}({rest_name});
}}
""".format(**capture))
EOF
)")
replace_in_file() {
  local file="$1"
  local pattern="$2"
  local replacement="$3"
  sed -i "s|$pattern|$(replacement/\n/\\n/)|g" "$file"
}
TYPEDEF=$(echo "$TMP" | grep "typedef __attribute__")
MEMBER_INIT=$(echo "$TMP" | grep "reinterpret_cast")
MEMBER_METHODS=$(echo "$TMP" | grep "WindowsLibrary::SetupCall" -B1 -A2 | sed "s/^--$//")
MEMBER_DECLS=$(echo "$TMP" | grep "// for")
EXTER_FUNCS=$(echo "$TMP" | grep 'extern "C"' -A2 | sed "s/^--$//")

# # replace in linoodle.cpp
sed -i "s|^\s*___TYPEDEF___;$|${TYPEDEF//$'\n'/\\n}|g" linoodle.cpp
sed -i "s|^\s*___MEMBER_INIT___;$|${MEMBER_INIT//$'\n'/\\n}|g" linoodle.cpp
sed -i "s|^\s*___MEMBER_METHODS___;$|${MEMBER_METHODS//$'\n'/\\n}|g" linoodle.cpp
sed -i "s|^\s*___MEMBER_DECLS___;$|${MEMBER_DECLS//$'\n'/\\n}|g" linoodle.cpp
sed -i "s|^\s*___EXTERN_FUNCS___;$|${EXTER_FUNCS//$'\n'/\\n}|g" linoodle.cpp
sed -i 's/"oo2core_8_win64.dll"/"oo2core_6_win64.dll"/g' linoodle.cpp

mkdir -p build && cd build && cmake .. && make -j4
