# %%
from _common import *
import polars as pl
import streamlit as st

setup_clr()
config = load_config()
dst_dir = config['unpack']['stage1_dir']
tags = ["Data0", "Data1", "Data2", "Data3", "DLC"]

import UnpackHelper # type: ignore
import SoulsFormats # type: ignore
# %%
df = pl.read_parquet("scripts/res/unpack_stage1.parquet").filter(
  (pl.col('on_disk_size').is_null() | pl.col('path').is_null()).not_()
).with_columns(
  segments = pl.col('path').str.strip_prefix('/').str.split('/'),
)

# %%
def split_path(path: str):
  return [s for s in path.split('/') if s]
def join_path(segments: list[str], *, is_dir: bool = False):
  segments = [s for s in segments if s]
  path = '/' + '/'.join(segments)
  if is_dir and not path.endswith('/'):
    path += '/'
  return path

def query(df: pl.DataFrame, prefix: list[str] = []):
  prefix = [s for s in prefix if s]
  prefix_str = join_path(prefix, is_dir=True)
  print("query", prefix_str)
  df = df.filter(pl.col('path').str.starts_with(prefix_str)).select('path', 'segments')
  df = df.with_columns(
    remain_segments = pl.col("segments").list.slice(len(prefix)),
  ).with_columns(
    is_file = pl.col('remain_segments').list.len() == 1,
    next_segment = pl.col('remain_segments').list.get(0),
  ).sort('is_file', 'path')
  return df
query(df, ['']).group_by('next_segment').agg(
  count = pl.len(),
  file_count = pl.col('is_file').sum(),
  path = pl.last('path')
).sort('count')

# %%
st.title('Elden Ring Data Browser')

st.session_state.prefix = st.session_state.get('prefix', '')
st.text_input('Enter prefix to filter paths:', st.session_state.prefix, on_change=lambda new_prefix: set_prefix(new_prefix))

def set_prefix(new_prefix):
  st.session_state.prefix = new_prefix

filtered_df = query(df, split_path(st.session_state.prefix))

# st.write("Filtered DataFrame:")
# st.dataframe(filtered_df)

grouped_df = filtered_df.group_by('next_segment').agg(
  count=pl.len(),
  file_count=pl.col('is_file').sum(),
  path=pl.last('path')
).sort('count', 'next_segment')

st.button('..', on_click=lambda: set_prefix('/'.join(split_path(st.session_state.prefix)[:-1])))
for row in grouped_df.rows(named=True):
  next_segment = row['next_segment']
  st.button(next_segment, on_click=lambda: set_prefix(f"{st.session_state.prefix}/{next_segment}"))

st.dataframe(grouped_df)

# %%
