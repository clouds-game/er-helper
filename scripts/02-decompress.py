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
      print(f"Regulation version is not provided, use {regulation_version}")
    param.ApplyRegulationVersionedParamdef(paramDef, regulation_version)
  data = []
  schema = [(field.InternalName, regulation_version is None or field.IsValidForRegulationVersion(regulation_version)) for field in paramDef.Fields]
  for row in param.Rows:
    # todo when value is decimal, need to truncate the number
    tmp = [row.ID, str(row.Name)] + [cell_value(cell) for cell, (_, valid) in zip(row.Cells, schema) if valid]
    data.append(tmp)
  columns = ["id", "row_name"] + [name for name, valid in schema if valid]
  df = pl.DataFrame(data, schema=columns, orient='row')
  if (df['row_name'] == "").all(ignore_nulls=True) == False:
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
from typing import TypedDict, Unpack
class Unpackargs(TypedDict):
  just_trace: bool
  save_dcx_res: bool

def hash_path(path: PathLike) -> str:
  import hashlib
  data = Path(path).as_posix().encode('utf-8')
  return hashlib.sha256(data).hexdigest()

def create_new_df() -> pl.DataFrame:
  df = pl.DataFrame(schema={"src": pl.String, "src_hash": pl.String, "dst": pl.String, "dst_hash": pl.String, "extra": pl.String})
  return df

def get_relative_path(path: PathLike, bases: list[PathLike]) -> Path:
  for base in bases:
    if Path(path).is_relative_to(base):
      return Path(path).relative_to(base)
  return Path(path)

def add_rows_to_df(df: pl.DataFrame, rows: list[tuple[PathLike, PathLike, str|None]]):
  data = []
  for row in rows:
    src = get_relative_path(Path(row[0]), [stage1_dir, stage2_dir])
    dst = get_relative_path(Path(row[1]), [stage2_dir])
    data.append([src.as_posix(), hash_path(src), dst.as_posix(), hash_path(dst), row[2]])
  df_t = pl.DataFrame(data, schema=["src", "src_hash", "dst", 'dst_hash', 'extra'], orient='row')
  df.vstack(df_t, in_place=True)

def add_row_to_df(df: pl.DataFrame, src: PathLike, dst: PathLike, extra: str|None = None):
  add_rows_to_df(df, [(src, dst, extra)])

def create_df(src: PathLike, dst: PathLike, extra: str|None = None) -> pl.DataFrame:
  df = create_new_df()
  add_row_to_df(df, src, dst, extra)
  return df

def bytes_to_clr(data: bytes | System.Array[System.Byte], *, path: PathLike | None = None):
  if data is None:
    if path:
      return System.IO.File.ReadAllBytes(str(path))
    return None
  return System.Array[System.Byte](data)

def unpack_fmg(path: PathLike, dst_dir: PathLike, data=None, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame:
  # print(f"Unpack FMG {path}")
  logger.info(f"Unpack FMG {path}")
  path, dst_dir = Path(path), Path(dst_dir)
  data = bytes_to_clr(data, path=path)
  fmg: SoulsFormats.FMG = UnpackHelper.Format[SoulsFormats.FMG].OpenInMemory(data)
  entries = [{"id":entry.ID,"text": entry.Text} for entry in fmg.Entries]
  target_path = dst_dir.joinpath(f"{path.stem}.json")
  target_path.parent.mkdir(parents=True, exist_ok=True)
  with open(target_path, "w", encoding='utf-8') as f:
    json.dump(entries, f, indent=2, ensure_ascii=False)
  logger.info(f"[FMG] Unpack {path} to {target_path}")
  df = create_df(path, target_path)
  return df


def unpack_tpf(path: PathLike, dst_dir: PathLike, data=None, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame:
  # print(f"Unpack TPF {path}")
  logger.info(f"Unpack TPF {path}")
  path, dst_dir = Path(path), Path(dst_dir)
  # dst_dir = dst_dir.joinpath(path.stem.replace('.', '-'))
  data = bytes_to_clr(data, path=path)
  tpf: SoulsFormats.TPF = UnpackHelper.Format[SoulsFormats.TPF].OpenInMemory(data)
  dst_dir.mkdir(parents=True, exist_ok=True)
  df = create_new_df()
  df_data = []
  for texture in tpf.Textures:
    target_path = dst_dir.joinpath(f"{texture.Name}.dds")
    df_data.append([str(path), str(target_path), texture.Name])
    if kwargs.get("just_trace", True):
      continue
    System.IO.File.WriteAllBytes(str(target_path), texture.Headerize())
  add_rows_to_df(df, df_data)
  return df

def unpack_binder(binder: SoulsFormats.BinderReader, dst_dir: PathLike, path: PathLike, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame:
  dst_dir, path = Path(dst_dir), Path(path)
  # dst_dir = dst_dir.joinpath(path.stem.replace('.', '-'))
  df = create_new_df()
  for file in binder.Files:
    data = binder.ReadFile(file)
    # target_path = dst_dir.joinpath(f"{str(file.Name).split('\\')[-1]}")
    (sub_path, root) = _utils.UnrootBNDPath(file.Name)
    if root:
      target_path = Path(stage2_dir).joinpath(sub_path)
    else:
      target_path = dst_dir.joinpath(sub_path)
    if data is None:
      logger.error(f"[{path.name}] Failed to read {file.Name}")
      continue
    add_row_to_df(df, path, target_path, extra=str(file.Name))
    df_child = unpack(target_path, target_path.parent, data, **kwargs)
    if df_child is not None:
      df.vstack(df_child, in_place=True)
      continue
    if kwargs.get("just_trace", True):
      continue
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    System.IO.File.WriteAllBytes(str(target_path), data)
  return df


def unpack_bnd4(path: PathLike, dst_dir: PathLike, data=None, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame:
  path, dst_dir = Path(path), Path(dst_dir)
  # print(f"Unpack BND4 {path}")
  logger.info(f"Unpack BND4 {path}")
  data = bytes_to_clr(data, path=path)
  bnd = SoulsFormats.BND4Reader(data)
  df = unpack_binder(bnd, dst_dir, path, **kwargs)
  return df


def unpack_bxf4(bhd_path: PathLike, dst_dir: PathLike, data=None, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame:
  bhd_path, dst_dir = Path(bhd_path), Path(dst_dir)
  # print(f"Unpack BHF4 {bhd_path}")
  logger.info(f"Unpack BHF4 {bhd_path}")
  bdt_path = Path(str(bhd_path).replace("bhd", "bdt"))
  bxf = SoulsFormats.BXF4Reader(str(bhd_path), str(bdt_path))
  df = unpack_binder(bxf, dst_dir, bhd_path, **kwargs)
  return df


def unpack_dcx(path: PathLike, dst_dir: PathLike, data=None, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame:
  # print(f"Unpack DCX {path}")
  logger.info(f"Unpack DCX {path}")
  path, dst_dir = Path(path), Path(dst_dir)
  compression = SoulsFormats.DCX.Type.Unknown
  if data:
    # print("csharp_bytes from data")
    (csharp_bytes, compression) = SoulsFormats.DCX.Decompress(data, compression)
  else:
    # print("csharp_bytes from path")
    (csharp_bytes, compression) = SoulsFormats.DCX.Decompress(str(path), compression)
  if kwargs.get("save_dcx_res", False):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_path = dst_dir.joinpath(path.stem)
    System.IO.File.WriteAllBytes(str(dst_path), csharp_bytes)
  df = unpack(path, dst_dir, data=csharp_bytes, **kwargs)
  return df


def unpack(path: PathLike, dst_dir: PathLike, data = None, **kwargs: Unpack[Unpackargs]) -> pl.DataFrame | None:
  format = _utils.get_format(data, path)
  data = bytes_to_clr(data, path=path)
  match format:
    case "DCX":
      return unpack_dcx(path, dst_dir, data=data, **kwargs)
    case "BND4":
      return unpack_bnd4(path, dst_dir, data=data, **kwargs)
    case "BHF4":
      return unpack_bxf4(path, dst_dir, data=data, **kwargs)
    case "BDF4":
      # appear with BHF4
      return None
    case "TPF":
      return unpack_tpf(path, dst_dir, data=data, **kwargs)
    case "FMG":
      return unpack_fmg(path, dst_dir, data=data, **kwargs)
    case _:
      # logger.warning(f"[ unpack ] Unknown format: {format}, path: {path}")
      # print(f"[ unpack ] Unknown format: {format}, path: {path}")
      return None




# %%
import sys
UnpackHelper.NativeLibrary.AddToPath(sys.path)
UnpackHelper.Helper.LoadOodle()

# %%

def trace_files(relative_files: list[PathLike], progress: bool = True) -> pl.DataFrame:
  if progress:
    import tqdm
    bar = tqdm.tqdm(total=len(relative_files), unit='file', desc='Trace')
  df = create_new_df()
  unknown_files = []
  for file in relative_files:
    if progress: bar.update(1)

    path = Path(f"{stage1_dir}").joinpath(file)
    dst_file = Path(f"{stage2_dir}").joinpath(file)
    dst_dir = dst_file.parent
    df_t = unpack(path, dst_dir, just_trace=True, save_dcx_res=False)
    if df_t is not None:
      df.vstack(df_t, in_place=True)
    else:
      unknown_files.append(file.as_posix())

  df_data = [(file, file, None) for file in unknown_files]
  add_rows_to_df(df, df_data)
  return df


from collections import defaultdict
src_dir = Path(f"{stage1_dir}")
allfiles = [file for file in list(src_dir.rglob('*')) if file.is_file()]


bucket = defaultdict(list)
bucket_size = 8
for file in allfiles:
  relative_path = file.relative_to(stage1_dir)
  key = int(hash_path(relative_path), 16) % bucket_size
  bucket[key].append(relative_path)
for k in range(bucket_size):
  files = bucket[k]
  files.sort()
  if os.path.exists(f"logs/trace_{k}.csv"):
    logger.warning(f"Skipping bucket_{k}, remove logs/trace_{k}.csv to force trace")
    continue
  logger.info(f"Tracing bucket {k}")
  df = trace_files(files)
  df.write_csv(f"logs/trace_{k}.csv")

# %%
file = "map/m10/m10_00_00_00/l10_00_00_00.hkxbhd"
path = Path(f"{stage1_dir}").joinpath(file)
dst_file = Path(f"{stage2_dir}").joinpath(file)
dst_dir = dst_file.parent
df = unpack(path, dst_dir, just_trace=False, save_dcx_res=True)
df

# df_suffix = df.with_columns(
#   suffix = pl.col('dst').str.split('.').list.last(),
# ).group_by('suffix').agg(
#   len = pl.col('dst').count(),
#   dst = pl.col('dst').last(),
# ).with_columns(
#   dst = pl.col('dst').str.split('\\').list.last()
# )
# df_unknown_suffix = pl.DataFrame(unknown_files, schema=["path"], orient='row').with_columns(
#   suffix = pl.col('path').str.split('.').list.slice(1).list.join('.'),
# ).group_by('suffix').agg(
#   len = pl.col('path').count(),
#   dst = pl.col('path').last(),
# )
# df_suffix


# %%
src_dir = Path(f"{stage1_dir}")
allfiles = list(src_dir.rglob('*'))
allfiles = [file for file in allfiles if file.is_file()]
print(len(allfiles))
df = pl.read_parquet("scripts/res/unpack_stage1.parquet")
print(len(df))
# %%



# %%
msg_src_dir = Path(f"{stage1_dir}/msg")
msg_dst_dir = Path(f"{stage2_dir}/msg")
for lang in ["zhocn", "jpnjp", "engus"]:
  for file in msg_src_dir.joinpath(lang).glob('*.dcx'):
    unpack_dcx(file, msg_dst_dir.joinpath(lang))

# %%
# todo 解压缩menu_icon 00_solo  fromats change in :  bnd -> dcx -> tpf -> dds
icons_src_dir = Path(f"{stage1_dir}/menu/hi/00_solo.tpfbhd")
icons_dst_dir = Path(f"{stage2_dir}/menu/hi/00_solo")
unpack_bxf4(icons_src_dir, icons_dst_dir)


# %%
icons_dst_dir = Path(f"{stage2_dir}/menu/hi/00_solo")
for file in icons_dst_dir.glob('*.dcx'):
  unpack_dcx(file, icons_dst_dir)

# %%
