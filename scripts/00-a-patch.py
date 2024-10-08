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
patch = """
diff --git a/StudioUtils/StudioUtils.csproj b/StudioUtils/StudioUtils.csproj
index 4bc4ef7..344d5a9 100644
--- a/StudioUtils/StudioUtils.csproj
+++ b/StudioUtils/StudioUtils.csproj
@@ -1,7 +1,7 @@
 <Project Sdk="Microsoft.NET.Sdk">

     <PropertyGroup>
-        <TargetFramework>net8.0-windows</TargetFramework>
+        <TargetFramework>net8.0</TargetFramework>
         <ImplicitUsings>enable</ImplicitUsings>
         <Nullable>enable</Nullable>
         <LangVersion>11</LangVersion>
diff --git a/WitchyFormats/WitchyFormats.csproj b/WitchyFormats/WitchyFormats.csproj
index 3c67687..14d1bf3 100644
--- a/WitchyFormats/WitchyFormats.csproj
+++ b/WitchyFormats/WitchyFormats.csproj
@@ -1,7 +1,7 @@
 <Project Sdk="Microsoft.NET.Sdk">

   <PropertyGroup>
-    <TargetFramework>net8.0-windows</TargetFramework>
+    <TargetFramework>net8.0</TargetFramework>
     <GenerateAssemblyInfo>true</GenerateAssemblyInfo>
     <IsPackable>false</IsPackable>
     <Title>WitchyFormats</Title>
"""
import subprocess
subprocess.run(["git", "apply"], input=patch.encode("utf-8"), cwd="vendor/WitchyBND")

# %%
patch = """
diff --git a/src/regulation/regulation.rs b/src/regulation/regulation.rs
index 49e680e..011b355 100644
--- a/src/regulation/regulation.rs
+++ b/src/regulation/regulation.rs
@@ -213,6 +213,7 @@ impl Regulation {
                 (11240023, 2001488),
                 (11310027, 2025152),
                 (11320031, 2019824),
+                (11410033, 2036288),
             ])
         })
     }
"""
import subprocess
subprocess.run(["git", "apply"], input=patch.encode("utf-8"), cwd="vendor/ER-Save-Lib")
# %%
