# %%
import os
import shutil
# os.chdir(os.path.dirname(os.path.dirname(__file__)))
# print(os.getcwd())

# %%
def copy_files(src: str, dst: str, *, files: list[str] = []):
  os.makedirs(dst, exist_ok=True)
  for file in files:
    src_file = f"{src}/{file}"
    dst_file = f"{dst}/{file}"
    if os.path.isdir(src_file):
      if not file.endswith("/"):
        file += '/'
    if not os.path.exists(os.path.dirname(dst_file)):
      os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    if file.endswith("/"):
      shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
    else:
      shutil.copy(f"{src}/{file}", f"{dst}/{file}")
copy_files("vendor/ER-Save-Lib", "libs/ER-Save-Lib", files=["src/", "Cargo.toml"])

# %%
import glob

for path in glob.glob("libs/ER-Save-Lib/**/*.rs", recursive=True):
  with open(path, "r", encoding='utf-8') as f:
    data = f.read()
  modified = False
  if "pub(crate)" in data:
    data = data.replace("pub(crate)", "pub")
    modified = True
  if path.endswith("lib.rs"):
    data = data.replace("mod save;", "pub mod save;").replace("pub pub ", "pub ")
    modified = True
  if modified:
    with open(path, "w") as f:
      print(f"modifying {path}")
      f.write(data)

# %%
src = "vendor/UXM-Selective-Unpack/UXM"
dst = "libs/UnpackHelper/src/UXM"
copy_files(src, dst, files=["ArchiveKeys.cs", "ArchiveDictionary.cs", "CryptographyUtility.cs"])
copy_files(src, "libs/UnpackHelper", files=["res/"])

for path in glob.glob("libs/UnpackHelper/src/UXM/**/*.cs", recursive=True):
  with open(path, "r") as f:
    data = f.read()
  modified = False
  if "private" in data:
    data = data.replace("private", "public")
    modified = True
  if "namespace UXM" in data:
    data = data.replace("namespace UXM", "namespace UnpackHelper.UXM")
    modified = True
  if modified:
    with open(path, "w") as f:
      print(f"modifying {path}")
      f.write(data)

# %%
