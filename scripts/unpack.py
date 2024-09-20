# %%
from _common import *

from dataclasses import dataclass
import polars as pl
import pythonnet
import sys, pathlib
enter_project_root()
logger = get_logger(__name__, filename=f'logs/unpack_{today_str()}.log')
pythonnet.load("coreclr")
sys.path.append(str(pathlib.Path("libs/UnpackHelper/bin/Debug/net8.0").absolute()))
import clr
for dll in ["UnpackHelper", "SoulsFormats"]:
  clr.AddReference(dll)
import SoulsFormats # type: ignore
import UnpackHelper # type: ignore
import System.IO # type: ignore

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
  for (f, r) in zip(file_headers, df.rows(named=True)):
    if r['path'] is None:
      logger.warning(f"[{tag}] Unknown name {r['FileNameHash']}")
      continue
    target_path = pathlib.Path(f"{dst_dir}/{r['path']}")
    if target_path.exists():
      logger.info(f"[{tag}] Skipping {target_path}")
      if progress:
        bar.update(r['PaddedFileSize'])
      continue
    try:
      data = f.ReadFile(stream)
      size = len(data) # data.Length
    except Exception as e:
      logger.error(f"[{tag}] Failed to read {r['path']}")
      raise e
    pathlib.Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    try:
      System.IO.File.WriteAllBytes(str(target_path), data)
    except Exception as e:
      logger.error(f"[{tag}] Failed to write {target_path}")
      os.remove(target_path)
      raise e
    logger.info(f"[{tag}] {target_path} size={size} hash={r['SHAHash']}")
    if progress:
      bar.update(r['PaddedFileSize'])

# %%
files = UnpackHelper.Helper.GetDictionary(game)
df_hash = pl.DataFrame([{'path':v,'hash':k} for k, v in dict(files).items()], schema_overrides={'hash': pl.UInt64})
df_hash

# %%
for tag in tags:
  path = f"{src_dir}/{tag}.bhd"
  logger.info(f"Unpacking {path}")
  df, file_headers = unpack_bhd(path, tag, hashes=df_hash)
  print(df)
  unpack_bdt(path, dst_dir, file_headers=file_headers, df=df)

# %%
