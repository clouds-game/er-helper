# %%
import os
os.chdir(os.path.dirname(os.path.dirname(__file__)))
print(os.getcwd())

# %%
import shutil
import os
def copy_crate(src: str, dst: str):
  os.makedirs(dst, exist_ok=True)
  shutil.copytree(f"{src}/src", f"{dst}/src", dirs_exist_ok=True)
  shutil.copy(f"{src}/Cargo.toml", f"{dst}/Cargo.toml")
copy_crate("vendor/ER-Save-Lib", "libs/ER-Save-Lib")

# %%
import glob

for path in glob.glob("libs/ER-Save-Lib/**/*.rs", recursive=True):
  with open(path, "r") as f:
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
