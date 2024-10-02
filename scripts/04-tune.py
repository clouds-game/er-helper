# %%
from _common import *

# enter_project_root()

ASSET_DIR = "tauri-app/assets"

df_bits = pl.read_csv(f"{ASSET_DIR}/eventflag_bst.csv")
df_bits

# %%
asset_name = "grace"
df = pl.read_csv(f"{ASSET_DIR}/{asset_name}.csv")
df = df.with_columns(
  block = pl.col('eventflag_id') // 1000,
  block_idx = pl.col('eventflag_id') % 1000,
).join(df_bits.select(block='from', offset='to'), on='block').with_columns(
  eventflag_id = pl.col('eventflag_id').cast(pl.UInt32),
  offset = (pl.col('offset') * 125 + pl.col('block_idx') // 8).cast(pl.UInt32),
  bit_mask = pl.lit(2).pow((7 - pl.col('block_idx') % 8)).cast(pl.UInt8),
).select(
  'id', 'map_id', 'eventflag_id', 'block', 'offset', 'bit_mask',
  name = pl.struct(pl.col("^name_.*$").name.map(lambda x: x.removeprefix("name_"))),
  map_name = pl.struct(pl.col("^mapname_.*$").name.map(lambda x: x.removeprefix("mapname_"))),
).filter(pl.col('map_id') > 0)
"""
Ouptut a json file with the following structure:
{
  "count": 100,
  "data": [
    {'id': 0, 'eventflag_id': 0, 'block': 0, 'offset': 0, 'bit_mask': 1},
  ],
  "text": {
    "zhocn": {
      "name": {
        0: "name_0",
      },
      "map_name": {
        0: "mapname_0",
      },
    },
  }
}
"""
names = {lang: dict(zip(df['id'], v)) for lang, v in df['name'].struct.unnest().to_dict().items()}
map_names = {lang: dict(zip(df['map_id'], v)) for lang, v in df['map_name'].struct.unnest().to_dict().items()}
result = {
  "count": df.height,
  "data": list(df.select('id', 'map_id', 'eventflag_id', 'block', 'offset', 'bit_mask').rows(named=True)),
  "text": {
    lang: dict(
      name=names[lang],
      map_name=map_names.get(lang, {})
    ) for lang in names.keys()
  },
}
print(asset_name, df.height, df.unique('eventflag_id').height)
with open(f"{ASSET_DIR}/{asset_name}.out.json", "w") as f:
  json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

# %%
asset_name = "boss"
df = pl.read_csv(f"{ASSET_DIR}/{asset_name}.csv")
df = df.with_columns(
  block = pl.col('eventflag_id') // 1000,
  block_idx = pl.col('eventflag_id') % 1000,
).join(df_bits.select(block='from', offset='to'), on='block').with_columns(
  eventflag_id = pl.col('eventflag_id').cast(pl.UInt32),
  offset = (pl.col('offset') * 125 + pl.col('block_idx') // 8).cast(pl.UInt32),
  bit_mask = pl.lit(2).pow((7 - pl.col('block_idx') % 8)).cast(pl.UInt8),
).select(
  'id', 'map_text_id', 'eventflag_id', 'block', 'offset', 'bit_mask',
  name = pl.struct(pl.col("^name_.*$").name.map(lambda x: x.removeprefix("name_"))),
  map_name = pl.struct(pl.col("^mapname_.*$").name.map(lambda x: x.removeprefix("mapname_"))),
).filter(pl.col('name').struct.field('engus').is_not_null()).unique(
  'eventflag_id', keep='first', maintain_order=True,
)

print(asset_name, df.height, df.unique('eventflag_id').height)
# if df.height != df.unique('eventflag_id').height:
#   print(df.group_by('eventflag_id').len().filter(pl.col('len') > 1).join(df, on='eventflag_id').sort('eventflag_id'))

names = {lang: dict(zip(df['id'], v)) for lang, v in df['name'].struct.unnest().to_dict().items()}
map_names = {lang: dict(zip(df['map_text_id'], v)) for lang, v in df['map_name'].struct.unnest().to_dict().items()}
result = {
  "count": df.height,
  "data": list(df.select('id', 'map_text_id', 'eventflag_id', 'block', 'offset', 'bit_mask').rows(named=True)),
  "text": {
    lang: dict(
      name=names[lang],
      map_name=map_names.get(lang, {})
    ) for lang in names.keys()
  },
}
with open(f"{ASSET_DIR}/{asset_name}.out.json", "w") as f:
  json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

# %%
asset_name = "weapon"
df = pl.read_csv(f"{ASSET_DIR}/{asset_name}.csv")
df = df.select(
  'id', 'icon_id', 'type', 'path',
  name = pl.struct(pl.col("^name_.*$").name.map(lambda x: x.removeprefix("name_"))),
).filter(
  pl.col('name').struct.field('engus').is_not_null() &
  (pl.col('name').struct.field('engus') != 'DLC dummy') &
  (pl.col('name').struct.field('engus') != '[ERROR]')
)
names = {lang: dict(zip(df['id'], v)) for lang, v in df['name'].struct.unnest().to_dict().items()}
result = {
  "count": df.height,
  "data": list(df.select('id', 'icon_id', 'type', 'path').rows(named=True)),
  "text": {
    lang: dict(name=names[lang]) for lang in names.keys()
  },
}
print(asset_name, df.height, df.unique('id').height)
with open(f"{ASSET_DIR}/{asset_name}.out.json", "w") as f:
  json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

# %%
