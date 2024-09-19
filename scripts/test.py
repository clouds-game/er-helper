# %%
from _common import *
import polars as pl

enter_project_root()

ASSET_DIR = "crates/tauri-app/src-tauri/assets";

# %%
df_bits = pl.read_csv(f"{ASSET_DIR}/eventflag_bst.csv")
df_bits

# %%
df = pl.read_csv(f"{ASSET_DIR}/graces.csv")
df = df.with_columns(
  block = pl.col('id') // 1000,
  block_idx = pl.col('id') % 1000,
).join(df_bits.select(block='from', offset='to'), on='block').with_columns(
  id = pl.col('id').cast(pl.UInt32),
  offset = (pl.col('offset') * 125 + pl.col('block_idx') // 8).cast(pl.UInt32),
  bit_mask = pl.lit(2).pow((7 - pl.col('block_idx') % 8)).cast(pl.UInt8),
)
df.group_by('block').len()

# %%
