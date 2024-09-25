#!/bin/env bash

workspace_dir=$(dirname $(dirname $(realpath $0)))
echo "Workspace directory: $workspace_dir"
cd "$workspace_dir/vendor/oodle-wrapper"

# git checkout . --recurse-submodules

# Apply patches
# # git diff --submodule=diff

# Add more methods
# oo2core_6_win64.dll
OODLE_26_API=$(cat <<EOF
extern "C" size_t OodleLZ_Decompress(uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, size_t dst_len, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t* dec_buf_base, size_t dec_buf_size, void* cb, void* cb_ctx, void* scratch, size_t scratch_size, int64_t thread_phase)
extern "C" size_t OodleLZ_Compress(int64_t codec, uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, int64_t level, void* opts, void* dictionary_base, void* lrm, void* scratch, size_t scratch_size)
extern "C" void* OodleLZ_CompressOptions_GetDefault(int64_t codec, int64_t level)
extern "C" size_t OodleLZ_GetCompressedBufferSizeNeeded(size_t src_len)
extern "C" size_t OodleLZ_GetDecodeBufferSize(size_t src_len, bool corruption_possible)
EOF
)

# oo2core_8_win64.dll
OODLE_28_API=$(cat <<EOF
extern "C" size_t OodleLZ_Decompress(uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, size_t dst_len, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t* dec_buf_base, size_t dec_buf_size, void* cb, void* cb_ctx, void* scratch, size_t scratch_size, int64_t thread_phase)
extern "C" size_t OodleLZ_Compress(int64_t codec, uint8_t* src_buf, size_t src_len, uint8_t* dst_buf, int64_t level, void* opts, void* dictionary_base, void* lrm, void* scratch, size_t scratch_size)
extern "C" void* OodleLZ_CompressOptions_GetDefault()
extern "C" size_t OodleLZ_GetCompressedBufferSizeNeeded(uint8_t unk, size_t src_len)
extern "C" size_t OodleLZ_GetDecodeBufferSize(uint8_t unk, size_t src_len, bool corruption_possible)
EOF
)

# echo "$OODLE_26_API" | sd 'extern "C" (?P<return>\w+\**) (?P<fn_name>\w+)\((?P<rest>((?P<arg_ty>\w+\**) (?P<arg_name>\w+), )*(?P<last_arg>.*))\)' '{"fn_name": "$fn_name", "return": "$return", "params": "$rest"} <<$arg_name: $arg_ty ++ $last_arg>>'

# output: typedef __attribute__((ms_abi)) size_t(*tDecompressFunc)(uint8_t * srcBuf, size_t srcLen, uint8_t * dstBuf, size_t dstLen, int64_t fuzz, int64_t crc, int64_t verbose, uint8_t * dstBase, size_t e, void * cb, void * cbCtx, void * scratch, size_t scratchSize, int64_t threadPhase);
generate() {
  local api_version=$1
  local api_minor_version=${api_version/^2//}
  local api_defs=$2
  local TMP=$(echo "$api_defs" | python -c "$(cat<<EOF
import sys, re
api_version = ${api_version}
for line in sys.stdin.readlines():
  capture = re.match(r'extern "C" (?P<return>\w+\**) (?P<fn_name>\w+)\((?P<rest>.*)\)', line).groupdict()
  assert capture, f"Failed to parse line: {line}"
  args = [tuple(s.strip().rsplit(' ', 1)) for s in capture['rest'].split(',') if s.strip()]
  base_name = capture['fn_name'].removeprefix('OodleLZ_')
  capture |= dict(
    api_version = api_version,
    rest_name = ", ".join(b for _, b in args),
    base_name = base_name,
    t_name = f"t{base_name}",
    m_name = f"m_{base_name}",
  )
  print("""
    typedef __attribute__((ms_abi)) {return} (*{t_name})({rest}); \\\\

    {m_name} = reinterpret_cast<{t_name}>(m_oodleLib.GetExport("{fn_name}")); \\\\

    {return} {base_name}({rest}) {{ \\\\
        WindowsLibrary::SetupCall(); \\\\
        return {m_name}({rest_name}); \\\\
    }} \\\\

    {t_name} {m_name}; /* for OODLE_{api_version}::{fn_name} */ \\\\

    extern "C" {return} {fn_name}({rest}) {{ \\\\
        return g_oodleWrapper.{base_name}({rest_name}); \\\\
    }} \\\\
""".format(**capture))
EOF
)")

  local TYPEDEF=$(echo "$TMP" | grep "typedef __attribute__")
  local MEMBER_INIT=$(echo "$TMP" | grep "reinterpret_cast")
  local MEMBER_METHODS=$(echo "$TMP" | grep "WindowsLibrary::SetupCall" -B1 -A2 | sed "s/^--$//" | grep -v '^$')
  local MEMBER_DECLS=$(echo "$TMP" | grep "/\* for OODLE_")
  local EXTER_FUNCS=$(echo "$TMP" | grep 'extern "C"' -A2 | sed "s/^--$//" | grep -v '^$')

  echo "Generated linoodle_${api_version}.h"
  cat > linoodle_${api_version}.h <<EOF
#pragma once

#define OODLE_API_VERSION ${api_version}
#define OODLE_DLL_NAME "oo2core_${api_minor_version}_win64.dll"

#define OODLE_API_DECLARE(component) __OODLE_API__##component##__

#define __OODLE_API__TYPEDEF__ \\
${TYPEDEF}
// #end define __OODLE_API__TYPEDEF__

#define __OODLE_API__MEMBER_INIT__ \\
${MEMBER_INIT}
// #end define __OODLE_API__MEMBER_INIT__

#define __OODLE_API__MEMBER_METHODS__ \\
${MEMBER_METHODS}
// #end define __OODLE_API__MEMBER_METHODS__

#define __OODLE_API__MEMBER_DECLS__ \\
${MEMBER_DECLS}
// #end define __OODLE_API__MEMBER_DECLS__

#define __OODLE_API__EXTERN_FUNCS__ \\
${EXTER_FUNCS}
// #end define __OODLE_API__EXTERN_FUNCS__
EOF
}
generate 26 "$OODLE_26_API"
generate 28 "$OODLE_28_API"


mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=RELEASE && make -j4

[[ -e liboodle_26.so ]] && cp liboodle_26.so "$workspace_dir/libs/UnpackHelper/lib/liboo2core_6_win64.so"
[[ -e liboodle_26.dylib ]] && cp liboodle_26.dylib "$workspace_dir/libs/UnpackHelper/lib/liboo2core_6_win64.dylib"

echo "$workspace_dir/libs/UnpackHelper/lib/liboo2core_6_win64.so"
