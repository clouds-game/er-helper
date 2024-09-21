# %%
from _common import *

from dataclasses import dataclass
import polars as pl
import pathlib

setup_clr()
logger = get_logger(__name__, filename=f'logs/trans_{today_str()}.log')

import SoulsFormats # type: ignore
import UnpackHelper # type: ignore
import System.IO # type: ignore

config = load_config()
src_dir = config['unpack']['stage1_dir']
dst_dir = config['unpack']['stage2_dir']

# %%

def is_csharp_byte_array(obj):
  try:
    # todo
    return str(obj.GetType().GetElementType()) == "System.Byte"
  except:
    return False

def unpack_param(path: pathlib.Path, dst_dir: pathlib.Path):
  ER_res_path = pathlib.Path("vendor/WitchyBND/WitchyBND/Assets/Paramdex/ER")
  paramdef_path = ER_res_path.joinpath(f"Defs/{path.stem}.xml")
  if not paramdef_path.exists():
      logger.warning(f"[param] Failed to find {paramdef_path}. Try use new name")
      newname = path.stem.rsplit('_',1)[0]
      paramdef_path = ER_res_path.joinpath(f"Defs/{newname}.xml")
      if not paramdef_path.exists():
          logger.error(f"[param] Failed to find {paramdef_path}. Skip")
          return
  param = SoulsFormats.SoulsFile[SoulsFormats.PARAM].Read(str(path))
  paramDef = SoulsFormats.PARAMDEF.XmlDeserialize(str(paramdef_path))
  if not param.ApplyParamdefCarefully(paramDef):
    logger.error(f"[param] Failed to apply paramdef to {path.name}")
    return
  data = []
  for row in param.Rows:
    # todo when value is decimal, need to truncate the number
    tmp = [System.Convert.ToHexString(cell.Value) if is_csharp_byte_array(cell.Value) else cell.Value for cell in row.Cells]
    tmp.insert(0, row.ID)
    data.append(tmp)
  schema = [field.InternalName for field in param.AppliedParamdef.Fields]
  schema.insert(0, 'id')
  df = pl.DataFrame(data,schema=schema,orient='row')
  target_path = pathlib.Path(f"{dst_dir}/{path.stem}.csv")
  target_path.parent.mkdir(parents=True, exist_ok=True)
  df.write_csv(target_path)


param_src_dir = pathlib.Path(f"{src_dir}/param/gameparam")
param_dst_dir = pathlib.Path(f"{dst_dir}/param/gameparam")
for file in param_src_dir.glob('*.param'):
  unpack_param(file, param_dst_dir)

# %%
