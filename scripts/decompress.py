# %%
from _common import *
import utils
from dataclasses import dataclass
import polars as pl
import pathlib
import json

setup_clr()
logger = get_logger(__name__, filename=f'logs/trans_{today_str()}.log')

import SoulsFormats # type: ignore
import UnpackHelper # type: ignore
import System.IO # type: ignore

config = load_config()
game_dir = config['unpack']['src_dir']
src_dir = config['unpack']['stage1_dir']
dst_dir = config['unpack']['stage2_dir']

# %%

def unpack_param(path: pathlib.Path, dst_dir: pathlib.Path):
  print("Unpack Param", path)
  ER_def_path = pathlib.Path("vendor/WitchyBND/WitchyBND/Assets/Paramdex/ER/Defs")
  exist_names = [path.stem for path in ER_def_path.glob("*.xml")]
  paramdef_name = utils.get_def_name(path.stem, exist_names)
  paramdef_path = ER_def_path.joinpath(f"{paramdef_name}.xml")
  if not paramdef_path.exists():
    logger.error(f"[param] [{path.stem}] Failed to find {paramdef_path}. Skip")
    return
  param = SoulsFormats.SoulsFile[SoulsFormats.PARAM].Read(str(path))
  paramDef = SoulsFormats.PARAMDEF.XmlDeserialize(str(paramdef_path))
  # if not param.ApplyParamdefCarefully(paramDef):
    # logger.error(f"[param] [{path.stem}] Failed to apply paramdef to {path.name}")
    # return
  param.ApplyParamdef(paramDef)
  data = []
  for row in param.Rows:
    # todo when value is decimal, need to truncate the number
    tmp = [System.Convert.ToHexString(cell.Value) if utils.is_csharp_byte_array(
        cell.Value) else cell.Value for cell in row.Cells]
    tmp.insert(0, row.ID)
    data.append(tmp)
  schema = [field.InternalName for field in param.AppliedParamdef.Fields]
  schema.insert(0, 'id')
  df = pl.DataFrame(data, schema=schema, orient='row')
  target_path = pathlib.Path(f"{dst_dir}/{path.stem}.csv")
  target_path.parent.mkdir(parents=True, exist_ok=True)
  df.write_csv(target_path)
  logger.info(f"[param] [{path.stem}] Unpack {path} to {target_path}")

# %%
param_src_dir = pathlib.Path(f"{src_dir}/param/gameparam")
param_dst_dir = pathlib.Path(f"{dst_dir}/param/gameparam")
for file in param_src_dir.glob('*.param'):
  unpack_param(file, param_dst_dir)

# %%
def read_csharp_bytes(path: pathlib.Path):
  with open(path, "rb") as f:
      file_bytes = f.read()
  csharp_bytes = System.Array[System.Byte](file_bytes)
  return csharp_bytes

def unpack_fmg(path: pathlib.Path, dst_dir: pathlib.Path, csharp_bytes=None):
  print(f"Unpack FMG {path}")
  # logger.info(f"Unpack FMG {path.name}")
  if not csharp_bytes:
    csharp_bytes = read_csharp_bytes(path)
  fmg = SoulsFormats.SoulsFile[SoulsFormats.FMG].Read(csharp_bytes)
  data = [{"id":entry.ID,"text": entry.Text} for entry in fmg.Entries]
  target_path = dst_dir.joinpath(f"{path.stem}.json")
  pathlib.Path(target_path).parent.mkdir(parents=True, exist_ok=True)
  with open(target_path, "w", encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  logger.info(f"[FMG] Unpack {path} to {target_path}")

def unpack_tpf(path: pathlib.Path, dst_dir: pathlib.Path, csharp_bytes=None):
  print(f"Unpack TPF {path}")
  # logger.info(f"Unpack FMB {path}")
  if not csharp_bytes:
    csharp_bytes = read_csharp_bytes(path)
  tpf = SoulsFormats.SoulsFile[SoulsFormats.TPF].Read(csharp_bytes)
  dst_dir.mkdir(parents=True, exist_ok=True)
  for texture in tpf.Textures:
    target_path = dst_dir.joinpath(f"{texture.Name}.dds")
    System.IO.File.WriteAllBytes(str(target_path), texture.Headerize())


def unpack_bnd4(path: pathlib.Path, dst_dir: pathlib.Path, csharp_bytes=None):
  # 这里有个问题 bnd4文件名是包含路径的 直接根据路径来存
  # 还是只取单纯的文件名  根据提供的路径来存储(目前是这种)
  print(f"Unpack BND4 {path}")
  logger.info(f"Unpack BND4 {path}")
  if not csharp_bytes:
    with open(path, "rb") as f:
      file_bytes = f.read()
    csharp_bytes = System.Array[System.Byte](file_bytes)
  bnd = SoulsFormats.BND4Reader(csharp_bytes)
  for file in bnd.Files:
    # (sub_path, root) = utils.UnrootBNDPath(file.Name)
    data = bnd.ReadFile(file)
    target_path = dst_dir.joinpath(f"{pathlib.Path(file.Name).name}")
    if file.Name.endswith(".fmg"):
      unpack_fmg(target_path, dst_dir, data)
    else:
      pathlib.Path(target_path).parent.mkdir(parents=True, exist_ok=True)
      System.IO.File.WriteAllBytes(str(target_path), data)
      logger.info(f"[{path.name}] Unpack {file.Name} to {target_path}")


def unpack_dcx(path: pathlib.Path, dst_dir: pathlib.Path, just_unzip = False):
  print(f"Unpack DCX {path}")
  logger.info(f"Unpack DCX {path}")
  # to load oo2core_6_win64.dll
  os.environ['PATH'] = os.environ.get('PATH', '') + os.pathsep + game_dir
  compression = SoulsFormats.DCX.Type.Unknown
  (csharp_bytes, compression) = SoulsFormats.DCX.Decompress(str(path), compression)
  if just_unzip:
    target_path = dst_dir.joinpath(f"{path.stem}")
    System.IO.File.WriteAllBytes(str(target_path), csharp_bytes)
  else:
    format = utils.get_format(bytes(csharp_bytes)[:10])
    match format:
      case "BND4":
        unpack_bnd4(path, pathlib.Path(dst_dir), csharp_bytes)
      case "TPF":
        unpack_tpf(path, pathlib.Path(dst_dir), csharp_bytes)
      case _:
        raise Exception(f"Unknown format {format}")

# %%
msg_src_dir = pathlib.Path(f"{src_dir}/msg")
msg_dst_dir = pathlib.Path(f"{dst_dir}/msg")
for lang in ["zhocn", "jpnjp", "engus"]:
  for file in msg_src_dir.joinpath(lang).glob('*.dcx'):
    unpack_dcx(file, msg_dst_dir.joinpath(lang))

# %%
path = pathlib.Path(f"D:/tmp/ER/menu/hi/01_common.tpf.dcx")
unpack_dcx(path, path.parent.joinpath(path.stem))
# %%
