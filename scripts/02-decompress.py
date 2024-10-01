# %%
from _common import *
import _utils
import json

setup_clr()
logger = get_logger(__name__, filename=f'logs/decompress_{today_str()}.log')

import SoulsFormats
import WitchyFormats
import UnpackHelper
import System.IO

config = load_config()
game_dir = config['unpack']['src_dir']
stage1_dir = config['unpack']['stage1_dir']
stage2_dir = config['unpack']['stage2_dir']

# %%
def cell_value(cell: WitchyFormats.PARAM.Cell):
  if cell is None:
    return None
  if _utils.is_csharp_byte_array(cell.Value):
    return System.Convert.ToHexString(cell.Value)
  return cell.Value
def row_offset(row: WitchyFormats.PARAM.Row):
  return row.GetType().GetField("DataOffset", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).GetValue(row)

def unpack_param(path: PathLike, dst_dir: PathLike, defs_path: PathLike = "vendor/WitchyBND/WitchyBND/Assets/Paramdex/ER/Defs", regulation_version: int | None = 0):
  print("Unpack Param", path)
  path, dst_dir, defs_path = Path(path), Path(dst_dir), Path(defs_path)
  exist_names = [path.stem for path in defs_path.glob("*.xml")]
  paramdef_name = _utils.get_def_name(path.stem, exist_names)
  paramdef_path = defs_path.joinpath(f"{paramdef_name}.xml")
  if not paramdef_path.exists():
    logger.error(f"[param] [{path.stem}] Failed to find {paramdef_path}. Skip")
    return
  param = UnpackHelper.Format[WitchyFormats.PARAM].OpenFile(str(path))
  paramDef = WitchyFormats.PARAMDEF.XmlDeserialize(str(paramdef_path), regulation_version is not None)
  # if not param.ApplyParamdefCarefully(paramDef):
    # logger.error(f"[param] [{path.stem}] Failed to apply paramdef to {path.name}")
    # return
  if regulation_version is None:
    param.ApplyParamdef(paramDef)
  else:
    if regulation_version == 0:
      regulation_version = max(*[i.RemovedRegulationVersion for i in paramDef.Fields], *[i.FirstRegulationVersion for i in paramDef.Fields])
      if regulation_version != 0:
        print(f"Regulation version is not provided, use {regulation_version}")
    param.ApplyRegulationVersionedParamdef(paramDef, regulation_version)
  data = []
  schema = [(field.InternalName, regulation_version is None or field.IsValidForRegulationVersion(regulation_version)) for field in paramDef.Fields]
  for row in param.Rows:
    # todo when value is decimal, need to truncate the number
    tmp = [row.ID, str(row.Name) if row.Name is not None else ""] + [cell_value(cell) for cell, (_, valid) in zip(row.Cells, schema) if valid]
    data.append(tmp)
  columns = ["id", "row_name"] + [name for name, valid in schema if valid]
  df = pl.DataFrame(data, schema=columns, orient='row')
  if df["row_name"].dtype == pl.Null or ((df['row_name'] == "") | (df["row_name"].is_null())).all():
    df = df.drop('row_name')
  # df = df.with_columns(
  #   __offset = pl.Series(values=[row_offset(row) for row in param.Rows], dtype=pl.UInt32),
  # )
  target_path = Path(f"{dst_dir}/{path.stem}.csv")
  target_path.parent.mkdir(parents=True, exist_ok=True)
  df.write_csv(target_path)
  logger.info(f"[param] [{path.stem}] Unpack {path} to {target_path}")


# %%
param_src_dir = Path(f"{stage1_dir}/param/gameparam")
param_dst_dir = Path(f"{stage2_dir}/param/gameparam")
for file in param_src_dir.glob('*.param'):
  unpack_param(file, param_dst_dir)

# %%
def bytes_to_clr(data: bytes | System.Array[System.Byte], *, path: PathLike | None = None):
  if not data:
    if path:
      return System.IO.File.ReadAllBytes(str(path))
    return None
  return System.Array[System.Byte](data)

def unpack_fmg(path: PathLike, dst_dir: PathLike, data=None):
  print(f"Unpack FMG {path}")
  path, dst_dir = Path(path), Path(dst_dir)
  # logger.info(f"Unpack FMG {path.name}")
  data = bytes_to_clr(data, path=path)
  fmg: SoulsFormats.FMG = UnpackHelper.Format[SoulsFormats.FMG].OpenInMemory(data)
  data = [{"id":entry.ID,"text": entry.Text} for entry in fmg.Entries]
  target_path = dst_dir.joinpath(f"{path.stem}.json")
  target_path.parent.mkdir(parents=True, exist_ok=True)
  with open(target_path, "w", encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  logger.info(f"[FMG] Unpack {path} to {target_path}")


def unpack_tpf(path: PathLike, dst_dir: PathLike, data=None):
  print(f"Unpack TPF {path}")
  path, dst_dir = Path(path), Path(dst_dir)
  # logger.info(f"Unpack TPF {path}")
  data = bytes_to_clr(data, path=path)
  tpf: SoulsFormats.TPF = UnpackHelper.Format[SoulsFormats.TPF].OpenInMemory(data)
  dst_dir.mkdir(parents=True, exist_ok=True)
  for texture in tpf.Textures:
    target_path = dst_dir.joinpath(f"{texture.Name}.dds")
    System.IO.File.WriteAllBytes(str(target_path), texture.Headerize())

def unpack_binder(binder: SoulsFormats.BinderReader, dst_dir: PathLike, path: PathLike):
  dst_dir, path = Path(dst_dir), Path(path)
  for file in binder.Files:
    data = binder.ReadFile(file)
    # (sub_path, root) = _utils.UnrootBNDPath(file.Name)
    logger.info(f"[origin name] {file.Name}")
    # N:\GR\data\INTERROOT_win64\msg\zhoCN\AccessoryInfo.fmg
    target_path = dst_dir.joinpath(f"{str(file.Name).split('\\')[-1]}")
    if data is None:
      logger.error(f"[{path.name}] Failed to read {file.Name}")
      continue
    if file.Name.endswith(".fmg"):
      unpack_fmg(target_path, dst_dir, data)
    else:
      Path(target_path).parent.mkdir(parents=True, exist_ok=True)
      System.IO.File.WriteAllBytes(str(target_path), data)
      logger.info(f"[{path.name}] Unpack {file.Name} to {target_path}")


def unpack_bnd4(path: PathLike, dst_dir: PathLike, data=None):
  # 这里有个问题 bnd4文件名是包含路径的 直接根据路径来存
  # 还是只取单纯的文件名  根据提供的路径来存储(目前是这种)
  path, dst_dir = Path(path), Path(dst_dir)
  print(f"Unpack BND4 {path}")
  logger.info(f"Unpack BND4 {path}")
  data = bytes_to_clr(data, path=path)
  bnd = SoulsFormats.BND4Reader(data)
  unpack_binder(bnd, dst_dir, path)


def unpack_bxf4(bhd_path: PathLike, dst_dir: PathLike):
  bhd_path, dst_dir = Path(bhd_path), Path(dst_dir)
  print(f"Unpack BND4 {bhd_path}")
  logger.info(f"Unpack BND4 {bhd_path}")
  bdt_path = Path(str(bhd_path).replace("bhd", "bdt"))
  bxf = SoulsFormats.BXF4Reader(str(bhd_path), str(bdt_path))
  unpack_binder(bxf, dst_dir, bhd_path)


def unpack_dcx(path: PathLike, dst_dir: PathLike, just_unzip = False):
  print(f"Unpack DCX {path}")
  logger.info(f"Unpack DCX {path}")
  path, dst_dir = Path(path), Path(dst_dir)
  compression = SoulsFormats.DCX.Type.Unknown
  (csharp_bytes, compression) = SoulsFormats.DCX.Decompress(str(path), compression)
  if just_unzip:
    target_path = dst_dir.joinpath(f"{path.stem}")
    System.IO.File.WriteAllBytes(str(target_path), csharp_bytes)
  else:
    format = _utils.get_format(bytes(csharp_bytes)[:10])
    match format:
      case "BND4":
        unpack_bnd4(path, dst_dir, csharp_bytes)
      case "TPF":
        unpack_tpf(path, dst_dir, csharp_bytes)
      case _:
        raise Exception(f"Unknown format {format}")


# %%
import sys
UnpackHelper.NativeLibrary.AddToPath(sys.path)
UnpackHelper.Helper.LoadOodle()

msg_src_dir = Path(f"{stage1_dir}/msg")
msg_dst_dir = Path(f"{stage2_dir}/msg")
for lang in ["zhocn", "jpnjp", "engus"]:
  for file in msg_src_dir.joinpath(lang).glob('*.dcx'):
    unpack_dcx(file, msg_dst_dir.joinpath(lang))

# %%
# todo 解压缩menu_icon 00_solo  fromats change in :  bnd -> dcx -> tpf -> bbs
icons_src_dir = Path(f"{stage1_dir}/menu/hi/00_solo.tpfbhd")
icons_dst_dir = Path(f"{stage2_dir}/menu/hi/00_solo")
unpack_bxf4(icons_src_dir, icons_dst_dir)

# %%
icons_dst_dir = Path(f"{stage2_dir}/menu/hi/00_solo")
for file in icons_dst_dir.glob('*.dcx'):
  unpack_dcx(file, icons_dst_dir)

# %%
