# %%
import importlib
import pythonnet
from pathlib import Path
import sys
pythonnet.load("coreclr")
# dotnet publish vendor/pythonnet-stub-generator/csharp/PythonNetStubGenerator
sys.path.extend(str(Path(i).absolute()) for i in [
  "vendor/pythonnet-stub-generator/csharp/PythonNetStubGenerator/bin/Release/netstandard2.0/publish",
  "libs/UnpackHelper/bin/Debug/net8.0",
])
import clr

modules = [
  "PythonNetStubGenerator",
  "SoulsFormats",
  "WitchyFormats",
  "UnpackHelper",
  "System.IO",
]
for module in modules:
  clr.AddReference(module)
  importlib.import_module(module)
import PythonNetStubGenerator # type: ignore
import System # type: ignore
additional_types = [
  System.Convert,
  System.Type,
  System.IO.File,
]

# %%
target_dir = Path("scripts/typings")
target_dir.mkdir(parents=True, exist_ok=True)
all_types: dict[str, System.Type] = {}
all_assemblies = System.AppDomain.CurrentDomain.GetAssemblies()
assembly = [a for a in all_assemblies if a.GetName().Name in modules]
for a in assembly:
  for ty in a.GetExportedTypes():
    all_types[f"{ty.Namespace}.{ty.Name}"] = ty
for ty in additional_types:
  ty = clr.GetClrType(ty)
  all_types[f"{ty.Namespace}.{ty.Name}"] = clr.GetClrType(ty)
for ty in all_types.values():
  PythonNetStubGenerator.PythonTypes.AddDependency(ty)
while True:
  dirty = PythonNetStubGenerator.PythonTypes.RemoveDirtyNamespace()
  namespace, types = dirty.Item1, dirty.Item2
  if namespace is None:
    break
  target_file = target_dir.joinpath(*namespace.split('.')) / "__init__.pyi"
  print(f"generating stubs for {namespace} in {target_file}")
  PythonNetStubGenerator.PythonTypes.ClearCurrent()
  text = PythonNetStubGenerator.StubWriter.GetStub(namespace, types)
  target_file.parent.mkdir(parents=True, exist_ok=True)
  with open(target_file, "w") as f:
    f.write(text)

# %%
