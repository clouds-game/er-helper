# %%
from _common import *

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
"""
<Enum Name="GOODS_TYPE" type="u8">
  <Option Value="0" Name="Normal Item" />
  <Option Value="1" Name="Key Item" />
  <Option Value="2" Name="Crafting Material" />
  <Option Value="3" Name="Remembrance" />
  <Option Value="4" Name="None" />
  <Option Value="5" Name="Sorcery" />
  <Option Value="6" Name="None" />
  <Option Value="7" Name="Spirit Summon - Lesser" />
  <Option Value="8" Name="Spirit Summon - Greater" />
  <Option Value="9" Name="Wondrous Physick" />
  <Option Value="10" Name="Wondrous Physick Tear" />
  <Option Value="11" Name="Regenerative Material" />
  <Option Value="12" Name="Info Item" />
  <Option Value="13" Name="None" />
  <Option Value="14" Name="Reinforcement Material" />
  <Option Value="15" Name="Great Rune" />
  <Option Value="16" Name="Incantation" />
  <Option Value="17" Name="Self Buff - Sorcery" />
  <Option Value="18" Name="Self Buff - Incantation" />
</Enum>
"""
df_goods_type = pl.DataFrame({
  "type_name": [
    "Normal", "KeyItem", "Crafting", "Remembrance", "None4",
    "Sorcery", "None6", "Spirit", "NamedSpirit",
    "Wondrous", "Tear", "Container",
    "Info", "None13", "Reinforcement", "GreatRune",
    "Incantation", "SorceryBuff", "IncantationBuff",
  ],
}).with_row_index().with_columns(index = pl.col('index').cast(pl.Int64))

asset_name = "goods"
df = pl.read_csv(f"{ASSET_DIR}/{asset_name}.csv")
df = df.select(
  'id', 'icon_id', 'type', 'path',
  name = pl.struct(pl.col("^name_.*$").name.map(lambda x: x.removeprefix("name_"))),
).filter(
  pl.col('name').struct.field('engus').is_not_null() &
  (pl.col('name').struct.field('engus') != 'DLC dummy') &
  (pl.col('name').struct.field('engus') != '[ERROR]')
).join(df_goods_type, left_on='type', right_on='index').with_columns(
  type = pl.coalesce(pl.col('type_name'), pl.col('type').cast(pl.String))
).drop('type_name')
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
