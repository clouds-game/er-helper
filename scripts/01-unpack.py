# %%
from _common import *

setup_clr()
logger = get_logger(__name__, filename=f'logs/unpack_{today_str()}.log')

import SoulsFormats
import UnpackHelper
import System.IO

config = load_config()
src_dir = config['unpack']['src_dir']
dst_dir = config['unpack']['stage1_dir']
tags = ["Data0", "Data1", "Data2", "Data3", "DLC"]
game = SoulsFormats.BHD5.Game.EldenRing
logger.info(f"Unpacking {game} {tags} from {src_dir} to {dst_dir}")
print(f"Unpacking {game} {tags} from {src_dir} to {dst_dir}")

# %%
@dataclass
class FileHeader:
  FileNameHash: int
  PaddedFileSize: int
  UnpaddedFileSize: int
  FileOffset: int
  SHAHash: str | None
  AESKey: str | None

  @staticmethod
  def from_net(f: SoulsFormats.BHD5.FileHeader):
    return FileHeader(
      FileNameHash=f.FileNameHash,
      PaddedFileSize=f.PaddedFileSize,
      UnpaddedFileSize=f.UnpaddedFileSize,
      FileOffset=f.FileOffset,
      SHAHash=System.Convert.ToHexString(f.SHAHash.Hash) if f.SHAHash else None,
      AESKey=System.Convert.ToHexString(f.AESKey.Key) if f.AESKey else None,
    )

def unpack_bhd(path: str, tag: str, hashes: pl.DataFrame):
  key = UnpackHelper.Helper.GetKey(game, tag)
  bhd5 = UnpackHelper.Helper.OpenHeader(game, path, key)
  file_headers = [f for b in bhd5.Buckets for f in b]
  df = pl.DataFrame([FileHeader.from_net(i) for i in file_headers], schema_overrides={'FileNameHash': pl.UInt64})
  df = df.join(hashes, left_on='FileNameHash', right_on='hash', how='left')
  return df, file_headers

def unpack_bdt(path: str, dst_dir: str, *, file_headers: list[SoulsFormats.BHD5.FileHeader], df: pl.DataFrame, progress: bool = True):
  stream = System.IO.File.OpenRead(path.replace(".bhd", ".bdt"))
  total_bytes = df['PaddedFileSize'].sum()
  tag = path.split('/')[-1].split('\\')[-1]
  if progress:
    import tqdm
    bar = tqdm.tqdm(total=total_bytes, unit='B', unit_scale=True, desc=tag)
  result: list[int | None] = []
  for (f, r) in zip(file_headers, df.rows(named=True)):
    result.append(None)
    if r['path'] is None:
      logger.warning(f"[{tag}] Unknown name {r['FileNameHash']}")
      continue
    target_path = Path(f"{dst_dir}/{r['path']}")
    if target_path.exists():
      logger.info(f"[{tag}] Skipping {target_path}")
      if progress: bar.update(r['PaddedFileSize'])
      try: result[-1] = target_path.stat().st_size
      except: pass
      continue
    try:
      data = f.ReadFile(stream)
      # actual_size = r['UnpaddedFileSize']
      # if len(data) > actual_size and actual_size > 0:
      #   data = data.Take(actual_size)
      size = len(data) # data.Length
    except Exception as e:
      logger.error(f"[{tag}] Failed to read {r['path']}")
      raise e
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    try:
      System.IO.File.WriteAllBytes(str(target_path), data)
    except Exception as e:
      logger.error(f"[{tag}] Failed to write {target_path}")
      os.remove(target_path)
      raise e
    logger.info(f"[{tag}] {target_path} size={size} hash={r['SHAHash']}")
    if progress: bar.update(r['PaddedFileSize'])
    result[-1] = size
  return result

# %%
files = UnpackHelper.Helper.GetDictionary(game)
df_hash = pl.DataFrame([{'path':v,'hash':k} for k, v in dict(files).items()], schema_overrides={'hash': pl.UInt64})
df_hash

# %%
for tag in tags:
  path = f"{src_dir}/{tag}.bhd"
  if os.path.exists(f"logs/unpack_{tag}.csv"):
    logger.warning(f"Skipping {path}, remove logs/unpack_{tag}.csv to force unpack")
    continue
  logger.info(f"Unpacking {path}")
  df, file_headers = unpack_bhd(path, tag, hashes=df_hash)
  print(df)
  on_disk_size = unpack_bdt(path, dst_dir, file_headers=file_headers, df=df)
  df = df.select(
    pack = pl.lit(tag),
    path = 'path',
    size = 'PaddedFileSize',
    actual_size = pl.col('UnpaddedFileSize').replace(0, None),
    on_disk_size = pl.Series(values=on_disk_size),
    checksum = 'SHAHash',
    path_hash = 'FileNameHash',
    offset = 'FileOffset',
    aes_key = 'AESKey',
  )
  print(df)
  df.write_csv(f"logs/unpack_{tag}.csv", quote_style="non_numeric")

# %%
df = pl.concat(pl.read_csv(f"logs/unpack_{tag}.csv", schema_overrides=dict(
  size = pl.UInt64, actual_size = pl.UInt64, on_disk_size = pl.UInt64, offset = pl.UInt64,
  path_hash = pl.UInt64, checksum = pl.String, aes_key = pl.String,
)) for tag in tags)
df.sort('path', nulls_last=True).write_parquet("scripts/res/unpack_stage1.parquet")

# %%
@dataclass
class BinderFile:
  ID: int
  Name: str
  CompressionType: str
  Flags: str

  def from_net(f: SoulsFormats.BinderFile):
    return BinderFile(
      ID=f.ID,
      Name=str(f.Name),
      CompressionType=str(f.CompressionType),
      Flags=str(f.Flags),
    )

def unpack_regulation(path: str, dst_dir: str):
  bnd = SoulsFormats.SFUtil.DecryptERRegulation(path)
  df = pl.DataFrame([BinderFile.from_net(f) for f in bnd.Files]).with_columns(
    Path = 'Name',
    Name = pl.col('Name').str.split('\\').list.last(),
  )
  result: list[int | None] = []
  for (file, meta) in zip(bnd.Files, df.rows(named=True)):
    result.append(None)
    target_path = Path(f"{dst_dir}/{meta['Name']}")
    if target_path.exists():
      logger.info(f"[regulation.bin] Skipping {target_path}")
      try: result[-1] = target_path.stat().st_size
      except: pass
      continue
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
      size = len(file.Bytes)
      System.IO.File.WriteAllBytes(str(target_path), file.Bytes)
    except Exception as e:
      logger.error(f"[regulation.bin] Failed to write {target_path}")
      os.remove(target_path)
      raise e
    result[-1] = size
    logger.info(f"[regulation.bin] {file.ID} {target_path} {file.Flags} {file.CompressionType}")
  df = df.select(
    id = 'ID',
    name = 'Name',
    size = pl.Series(values=result),
    compression = 'CompressionType',
    flag = 'Flags',
    path = 'Path',
  )
  df.write_csv(f"logs/unpack_regulation.csv", quote_style="non_numeric")

# %%
path = f"{src_dir}/regulation.bin"
regulation_dst_dir = f"{dst_dir}/param/gameparam"
print(f"Unpacking regulation.bin from {src_dir} to {regulation_dst_dir}")
logger.info(f"Unpacking regulation.bin from {src_dir} to {regulation_dst_dir}")
unpack_regulation(path, regulation_dst_dir)
# %%
