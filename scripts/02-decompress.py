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

from typing import TypeVar
FormatClass = TypeVar('T')
@dataclass
class File:
  path: str # relative path
  data: bytes | None = None
  fmt_from_data: str | None = None
  fmt_from_path: str | None = None
  fmt_executing: str | None = None
  parent_hash: str | None = None

  @property
  def hash(self):
    return _utils.hash_path(self.path, self.parent_hash)

  def format(self, stage_dir: PathLike = None):
    if self.fmt_executing:
      return self.fmt_executing
    if self.fmt_from_data is None:
      if stage_dir is None:
        fmt1, fmt2 = get_format(self.data or b"", self.path)
      else:
        fmt1, fmt2 = get_format(self.data, Path(stage_dir).joinpath(self.path))
      self.fmt_from_data = fmt1
      self.fmt_from_path = fmt2
    if self.fmt_from_data:
      return self.fmt_from_data
    return self.fmt_from_path

  def get_data(self, stage_dir: PathLike = None) -> bytes:
    if self.data is None and stage_dir is not None:
      path = Path(stage_dir).joinpath(self.path)
      self.data = bytes_to_clr(None, path=path)
    return self.data

  def open_as(self, fmt: type[FormatClass], fmt_str: str, stage_dir: PathLike = None, helper = False) -> FormatClass:
    data = self.get_data(stage_dir)
    if helper:
      result = UnpackHelper.Format[fmt].OpenInMemory(data)
    else:
      result = fmt(data)
    self.fmt_executing = fmt_str
    return result

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
# def add_rows_to_df(df: pl.DataFrame, rows: list[tuple[PathLike, PathLike, str|None]]):
#   data = []
#   for row in rows:
#     src = get_relative_path(Path(row[0]), [stage1_dir, stage2_dir])
#     dst = get_relative_path(Path(row[1]), [stage2_dir])
#     data.append([src.as_posix(), hash_path(src), dst.as_posix(), hash_path(dst), row[2]])
#   df_t = pl.DataFrame(data, schema=["src", "src_hash", "dst", 'dst_hash', 'extra'], orient='row')
#   df.vstack(df_t, in_place=True)

# def add_row_to_df(df: pl.DataFrame, src: PathLike, dst: PathLike, extra: str|None = None):
#   add_rows_to_df(df, [(src, dst, extra)])

@dataclass
class Metadata:
  path: PathLike
  extra: str
  size: int | None = None
  fmt_from_bytes: str | None = None

def normalize_path(path: PathLike):
  return Path(path).as_posix().lower()

def create_df(src: File, dst: list[Metadata]) -> pl.DataFrame:
  df = pl.DataFrame(
    [
      (normalize_path(src.path), src.hash, normalize_path(meta.path), _utils.hash_path(meta.path, src.hash), meta.extra, meta.size, src.format(), meta.fmt_from_bytes)
      for meta in dst
    ],
    schema={"src_path": pl.String, "src_hash": pl.String, "dst_path": pl.String, "dst_hash": pl.String, "original_path": pl.String, "size": pl.Int64, "method": pl.String, "fmt": pl.String},
    orient='row')
  return df

def bytes_to_clr(data: bytes | System.Array[System.Byte] | None, *, path: PathLike | None = None):
  if data is None:
    if path:
      return System.IO.File.ReadAllBytes(str(path))
    return None
  return System.Array[System.Byte](data)

@dataclass
class UnpackConfig:
  stage1_dir: Path
  stage2_dir: Path | None
  force: bool

  @property
  def just_trace(self):
    return self.stage2_dir is None


# %%
def unpack_fmg(file: File, config: UnpackConfig) -> pl.DataFrame:
  """
  fmg usually be a message file that decoded to .json
  """
  # print(f"Unpack FMG {path}")
  logger.info(f"Unpack FMG {file.path} from {file.parent_hash}")
  fmg = file.open_as(SoulsFormats.FMG, "FMG", stage_dir=config.stage1_dir, helper=True)
  entries = [{"id":entry.ID,"text": entry.Text} for entry in fmg.Entries]
  dst_path = Path(file.path).with_suffix(".json")
  if not config.just_trace:
    target_path = config.stage2_dir.joinpath(dst_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding='utf-8') as f:
      # TODO: jsonline like writer
      json.dump(entries, f, indent=2, ensure_ascii=False)
    logger.info(f"[FMG] Unpack {path} to {target_path}")
  return create_df(file, [Metadata(dst_path, None, fmt_from_bytes="JSON")])


def unpack_tpf(file: File, config: UnpackConfig) -> pl.DataFrame:
  """
  tpf is a texture package file, usually contains dds files
  """
  # print(f"Unpack TPF {path}")
  logger.info(f"Unpack TPF {file.path} from {file.parent_hash}")
  tpf = file.open_as(SoulsFormats.TPF, "TPF", stage_dir=config.stage1_dir, helper=True)
  dst_dir = Path(file.path).parent
  if not config.just_trace:
    target_dir = config.stage2_dir.joinpath(dst_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
  meta = []
  for texture in tpf.Textures:
    meta.append(Metadata(dst_dir.joinpath(f"{texture.Name}.dds"), str(texture.Name), fmt_from_bytes="DDS"))
    if not config.just_trace:
      target_path = target_dir.joinpath(f"{texture.Name}.dds")
      System.IO.File.WriteAllBytes(str(target_path), texture.Headerize())
  return create_df(file, meta)

def unpack_binder(binder: SoulsFormats.BinderReader, src_file: File, config: UnpackConfig) -> pl.DataFrame:
  """
  binder is a inner format that contains multiple files
  """
  # dst_dir = dst_dir.joinpath(path.stem.replace('.', '-'))
  meta = []
  dfs = []
  for file in binder.Files:
    data = binder.ReadFile(file)
    # target_path = dst_dir.joinpath(f"{str(file.Name).split('\\')[-1]}")
    (dst_path, root) = _utils.UnrootBNDPath(file.Name)
    if root is None:
      if dst_path.startswith("N:"):
        dst_path = Path(src_file.path).parent.joinpath(str(file.Name).split('\\')[-1])
      else:
        dst_path = Path(src_file.path).parent.joinpath(dst_path)
    if data is None:
      logger.error(f"[{path.name}] Failed to read {file.Name}")
      continue
    # print("--------")
    # print(path)
    # print(target_path)
    # print(len(data))
    inner_file = File(dst_path, data, parent_hash=src_file.hash)
    meta.append(Metadata(dst_path, file.Name, data.Length, fmt_from_bytes=inner_file.format()))
    df_child = unpack(inner_file, config)
    if df_child is not None:
      dfs.append(df_child)
      continue
    if not config.just_trace:
      target_path = Path(config.stage2_dir).joinpath(dst_path)
      target_path.parent.mkdir(parents=True, exist_ok=True)
      System.IO.File.WriteAllBytes(str(target_path), data)
  # TODO: file
  df = create_df(src_file, meta)
  df = pl.concat([df, *dfs])
  return df


def unpack_bnd4(file: File, config: UnpackConfig) -> pl.DataFrame:
  """
  bnd4 is a binder file that contains multiple files
  """
  logger.info(f"Unpack BND4 {file.path}")
  bnd = file.open_as(SoulsFormats.BND4Reader, "BND4", stage_dir=config.stage1_dir)
  df = unpack_binder(bnd, file, config)
  return df


def unpack_bxf4(file: File, config: UnpackConfig) -> pl.DataFrame:
  """
  bhd4 and bdt4 are a pair of files that contains multiple files
  """
  bhd_path = config.stage1_dir.joinpath(file.path)
  bdt_path = bhd_path.parent.joinpath(f"{bhd_path.stem}{bhd_path.suffix.replace('bhd', 'bdt')}")
  logger.info(f"Unpack BXF4 {bhd_path}")
  bxf = SoulsFormats.BXF4Reader(str(bhd_path), str(bdt_path))
  file.fmt_executing = "BXF4"
  df = unpack_binder(bxf, file, config)
  return df


def unpack_dcx(file: File, config: UnpackConfig) -> pl.DataFrame:
  """
  dcx is a compressed file that contains a inner file
  """
  logger.info(f"Unpack DCX {file.path}")
  compression = SoulsFormats.DCX.Type.Unknown
  data = file.get_data(stage_dir=config.stage1_dir)
  (csharp_bytes, compression) = SoulsFormats.DCX.Decompress(data, compression)
  file.fmt_executing = "DCX"
  inner_file = File(file.path, csharp_bytes, parent_hash=file.parent_hash)
  inner_file.format()
  df = None
  if inner_file.fmt_from_data:
    df = unpack(inner_file, config)
  if df is None:
    dst_path = Path(file.path).with_suffix("")
    if not config.just_trace:
      target_path = config.stage2_dir.joinpath(dst_path)
      target_path.parent.mkdir(parents=True, exist_ok=True)
      System.IO.File.WriteAllBytes(str(target_path), csharp_bytes)
    df = create_df(file, [Metadata(dst_path, None, csharp_bytes.Length)])
  return df

dict_unpack_formats = {
  "DCX": unpack_dcx,
  "BND4": unpack_bnd4,
  "BHF4": unpack_bxf4,
  "TPF": unpack_tpf,
  "FMG": unpack_fmg,
}

# %%
dict_suffix_mapping = {
  'entryfilelist': "ENFL",
}
def get_format_from_bytes(arr: bytes):
  magic = arr[:4].decode('ascii', errors='ignore')
  if magic in [
    "AISD", # .aisd
    "BDF3", "BDF4", # .bdt
    "BHF3", "BHF4", # .bhd
    "BND3", "BND4", # .bnd
    "DDS ", # .dds
    "DLSE", # .dlse
    "\0BRD", "DRB\0", # .drb
    "EDF\0", # .edf
    "ELD\0", # .eld
    "ENFL", # .entryfilelist
    "FSSL", # .esd
    "EVD\0", # .evd
    "DFPN", # .nfd
    "TAE ", # .tae
    "TPF\0", # .tpf
    "#BOM", # .txt
  ]:
    if magic == '\0BRD': magic = "DRB\0"
    if magic == "#BOM": magic = "TXT"
    return magic.upper().strip(' \0')
  if magic[:3] in [
    "FEV", # .fev
    "FSB", # .fsb
    "GFX", # .gfx
  ]:
    return magic[:3]
  if arr[:6] == b"FLVER\0": # .flver
    return "FLVER"
  if arr[1:4] == b"Lua": # .lua
    return "LUA"
  if arr[0xC:0xC+0xE] == b"ITLIMITER_INFO": # .itl
    return "ITL"
  if arr[0x2C:0x2C+4] == b"MTD ": # .mtd
    return "MTD"
  if arr[1:4] == b"PNG": # .png
    return "PNG"
  if arr[0x28:0x28+4] == b"SIB ": # .sib
    return "SIB"
  if arr[:5] == b"<?xml": # .xml
    return "XML"
  return None

def get_format(byte_array: bytearray, path: PathLike, detect_length = 0x40) -> tuple[str, str]:
  if byte_array is None:
    with open(path, "rb") as f:
      byte_array = f.read(detect_length)
  byte_array = System.Array[System.Byte](byte_array)
  if len(byte_array) > detect_length:
    byte_array = System.ArraySegment[System.Byte](byte_array, 0, min(detect_length, len(byte_array))).ToArray()
  if SoulsFormats.DCX.Is(byte_array):
    # TODO: should DCX be transparent
    guessed_ext = "DCX"
  else:
    guessed_ext = str(SoulsFormats.SFUtil.GuessExtension(byte_array))[1:].upper()
  if guessed_ext in ["BDT", "BHD", "BND"]:
    guessed_ext = "".join([chr(byte_array[i]) for i in range(4)])
  path_ext = Path(path).suffix[1:].upper()
  path_ext = dict_suffix_mapping.get(path_ext.lower(), path_ext)
  return guessed_ext, path_ext

def unpack(file: File, config: UnpackConfig) -> pl.DataFrame | None:
  format = file.format(stage_dir=config.stage1_dir)
  print("unpacking", file.path, format)
  if format in dict_unpack_formats:
    return dict_unpack_formats[format](file, config)

# %%
import sys
UnpackHelper.NativeLibrary.AddToPath(sys.path)
UnpackHelper.Helper.LoadOodle()

# %%
unpack_config = UnpackConfig(Path(stage1_dir), None, force=False)
dfs = []
for i, path in enumerate(Path(stage1_dir).joinpath("map").glob('*.*')):
  print(path)
  path = path.relative_to(stage1_dir)
  df = unpack(File(path), unpack_config)
  dfs.append(df)
dfs = [x for x in dfs if x is not None]
df = pl.concat(dfs)
df

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
file = "sfx/sfxbnd_c2120.ffxbnd.dcx"
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
