# %%
from dataclasses import dataclass
from _common import*
import pythonnet
import sys, pathlib
enter_project_root()
pythonnet.load("coreclr")
sys.path.append(str(pathlib.Path("libs/UnpackHelper/bin/Debug/net8.0").absolute()))
import clr
import importlib
for dll in ["UnpackHelper", "SoulsFormats"]:
  clr.AddReference(dll)
  module = importlib.import_module(dll)
  importlib.reload(module)
import SoulsFormats # type: ignore
import UnpackHelper # type: ignore
key = UnpackHelper.Helper.GetKey(SoulsFormats.BHD5.Game.EldenRing, "DLC")
files = UnpackHelper.Helper.GetDictionary(SoulsFormats.BHD5.Game.EldenRing)
files.Count

# %%
@dataclass
class Field:
  name: str
  type: str
  collectable: bool
  static: bool
  public: bool
  can_read: bool
  can_write: bool

  @staticmethod
  def from_field(f):
    return Field(
      name=f.Name,
      type=f.FieldType.Name,
      collectable=f.IsCollectible,
      static=f.IsStatic,
      public=f.IsPublic,
      can_read=True,
      can_write=True,
    )
  @staticmethod
  def from_property(p):
    return Field(
      name=p.Name,
      type=p.PropertyType.Name,
      collectable=p.CanRead,
      static=p.GetGetMethod().IsStatic,
      public=p.GetGetMethod().IsPublic,
      can_read=p.CanRead,
      can_write=p.CanWrite,
    )

  @staticmethod
  def collect_type(ty):
    return [Field.from_field(i) for i in ty.GetFields()] + [Field.from_property(i) for i in ty.GetProperties()]

  @staticmethod
  def to_dict(fields: list["Field"], instance):
    return {f.name: getattr(instance, f.name) for f in fields}

# %%
import polars as pl
df_hash = pl.DataFrame([{'path':v,'hash':k} for k, v in dict(files).items()], schema_overrides={'hash': pl.UInt64})
df_hash

# %%
path = "/mnt/d/Steam/steamapps/common/ELDEN RING/Game/DLC.bhd"
bhd5 = UnpackHelper.Helper.OpenHeader(SoulsFormats.BHD5.Game.EldenRing, path, key)

# %%
bhd5.Buckets.Count

# %%
file_headers = [f for b in bhd5.Buckets for f in b]
fields = Field.collect_type(file_headers[0].GetType())
df = pl.DataFrame([Field.to_dict(fields, i) for i in file_headers], schema_overrides={f.name: pl.String if f.type == "String" else pl.UInt64 for f in fields})
df = df.join(df_hash, left_on='FileNameHash', right_on='hash', how='left')
df

# %%
import System.IO # type: ignore
stream = System.IO.File.OpenRead(path.replace(".bhd", ".bdt"))
dst_dir = pathlib.Path("/mnt/d/tmp/ER")
logger = open("log.txt", "w")
for (f, r) in zip(file_headers, df.rows(named=True)):
  if r['path'] is None:
    continue
  target_path = dst_dir.joinpath(str(r['path']).removeprefix('/'))
  print(target_path, file=logger)
  data = f.ReadFile(stream)
  target_path.parent.mkdir(parents=True, exist_ok=True)
  System.IO.File.WriteAllBytes(str(target_path), data)
logger.close()

# %%
