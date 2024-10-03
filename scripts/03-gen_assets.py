# %%
import csv
from _common import *

logger = get_logger(__name__, filename=f'logs/gen_assets_{today_str()}.log')

config = load_config()
game_dir = config['unpack']['src_dir']
stage1_dir = config['unpack']['stage1_dir']
stage2_dir = Path(config['unpack']['stage2_dir'])

ASSET_DIR = "tauri-app/assets"
paramdex_dir = Path("vendor/WitchyBND/WitchyBND/Assets/Paramdex/ER")
langs = ['zhocn', 'jpnjp', 'engus']
Path(ASSET_DIR).mkdir(parents=True, exist_ok=True)

# %%
class Message:
  def __init__(self, df: pl.DataFrame, *, name: str, dlc_part: str = None):
    self.df = df
    self.name = name
    self.dlc_part = dlc_part

  @staticmethod
  def load(name: str, *, langs = langs, stage_dir = stage2_dir):
    file_name = name
    dlc_part = name.rsplit('_', 1)[-1]
    if dlc_part.startswith('dlc'):
      name = name.removesuffix('_' + dlc_part)
    else:
      dlc_part = None
    data: dict[str, list] = {}
    for lang in langs:
      path = Path(stage_dir).joinpath(f"msg/{lang}/{file_name}.json")
      with open(path, encoding='utf-8') as f:
        data[lang] = json.load(f)
    result = None
    for lang in langs:
      df = pl.DataFrame(data[lang], schema_overrides=dict(text=pl.String)).rename(dict(text=f'text_{lang}'))
      if result is None:
        result = df
      else:
        result = result.join(df, on='id', how='full', coalesce=True)
    df = result.select(
      pl.lit(name).alias('tag'),
      pl.lit(dlc_part, dtype=pl.String).alias('dlc'),
      pl.col('*'),
    )
    return Message(df, name=name, dlc_part=dlc_part)

  def __str__(self) -> str:
    return f"Message({self.name}: {self.df})"

  def __repr__(self) -> str:
    return f"Message({self.name}: {self.df.shape})"

  def __getitem__(self, index: str) -> pl.DataFrame:
    return self.df.filter(pl.col('tag') == index)#.unique(pl.all().exclude('dlc'), keep='last', maintain_order=True)

def msg_rename_with_prefix(prefix: str, langs = None):
  if langs is None:
    def _rename(col_name: str) -> str:
      return f'{prefix}_{col_name.removeprefix("text_")}' if col_name.startswith('text_') else col_name
    return _rename
  return {f'text_{lang}': f'{prefix}_{lang}' for lang in langs}

def read_paramdex_names(name: str, paramdex_dir: PathLike = paramdex_dir) -> list[dict]:
  with open(paramdex_dir / f"Names/{name}.txt") as f:
    lines = f.readlines()
  result: list[tuple[int, str]] = []
  for line in lines:
    id, name = line.split(' ', 1)
    result.append({'id': int(id), 'name': name.strip('\n')})
  return result

# msg__npc_name = Message.load('NpcName')
# msg__npc_name.df

def load_mesaages(name_list: list[str] = None, *, stage_dir = stage2_dir, langs=langs, dlc = True) -> Message:
  if name_list is None:
    name_list = [path.stem for path in stage_dir.joinpath('msg/jpnjp').glob('*.json')]
  elif dlc:
    name_list = [f"{name}{dlc}" for name in name_list for dlc in ['', '_dlc01', '_dlc02']]
  messages = [Message.load(name, langs=langs) for name in name_list]
  return Message(pl.concat([msg.df for msg in messages]), name=f'all[{len(name_list)}]')

msg_all = load_mesaages()
df_msg_all = msg_all.df

# %%
def gen_grace(stage_dir: PathLike, *, langs = langs):
  df_msg = load_mesaages(['PlaceName', 'GR_MenuText'], stage_dir=stage_dir)

  BonfireWarpParam_path = f"{stage_dir}/param/gameparam/BonfireWarpParam.csv"
  BonfireWarpSubCategoryParam_path = f"{stage_dir}/param/gameparam/BonfireWarpSubCategoryParam.csv"
  BonfireWarpParam = pl.read_csv(BonfireWarpParam_path).select(
    id = 'id',
    map_id = 'bonfireSubCategoryId',
    eventflag_id = 'eventflagId',
    text_id = 'textId1',
  )
  BonfireWarpSubCategoryParam = pl.read_csv(BonfireWarpSubCategoryParam_path).select(
    id = 'id', map_text_id = 'textId')
  df = BonfireWarpParam.join(
    BonfireWarpSubCategoryParam, left_on='map_id', right_on='id', how='left')
  langs_col = [f'text_{lang}' for lang in langs]
  df = df.join(df_msg['PlaceName'], left_on='text_id', right_on='id', suffix="_name", how='left').rename(
    msg_rename_with_prefix('name', langs)
  )
  df = df.join(df_msg['GR_MenuText'].select('id', *langs_col), left_on='map_text_id', right_on='id', suffix="_mapname", how='left').rename(
    msg_rename_with_prefix('mapname', langs)
  )
  assert(df.shape[0] == BonfireWarpParam.shape[0])
  return df
df_grace = gen_grace(stage2_dir)
df_grace.write_csv(f"{ASSET_DIR}/grace.csv", quote_style='non_numeric')

# %% Generate boss.csv
place_map = {
  'Liurnia Highway Far North': "Liurnia Highway North",
  'Liurnia - Meeting Place': "Temple Quarter",
  'Liurnia - Albinauric Village': 'Village of the Albinaurics',
  'Liurnia': 'Liurnia of the Lakes',
  'Bellum Highway - Minor Erdtree': 'Bellum Highway',

  'Weeping Peninsula - Castle Morne Approach North': "Castle Morne", # for "Death Rite Bird" and "Night's Cavalry" at 60_44_32
  #"Weeping Peninsula - Minor Erdtree": "Weeping Peninsula", # for "Erdtree Avatar" at 60_43_33

  'Gate Town Northwest': "Gate Town North",
  'Erdtree-Gazing Hill- Lux Ruins': "Erdtree-Gazing Hill",
  'Altus Plateau - Shaded Castle': "The Shaded Castle",
  #'Altus Plateau - Minor Erdtree': 'Altus Plateau',
  #'Altus Plateau - Tree Sentinel Duo': "Altus Plateau",
  #'Altus Plateau - South of Tree Sentinel Duo': "Altus Plateau", # for "Fallingstar Beast"

  'Caelid - West Sellia': "Sellia, Town of Sorcery", # for "Nox Swordress & Nok Monk" and "Battlenage"
  'Caelid - East Aeonia Swamp': "Swamp of Aeonia", # for "Commander O'Neil"
  'Southeast Caelid': "Caelid", # for "Starscourge Radahn"
  #"Greyoll's Dragonbarrow - Southeast Farum Greatbridge": "Greyoll's Dragonbarrow",

  'Mountaintops of the Giants - Before Grand Lift of Rold': "Forbidden Lands", # for "Black Blade Kindred"
  'Northeast Mountaintops': "Freezing Lake", # for "Borealis the Freezing Fog"
  'Mountaintops of the Giants - West of Castle Sol': "Castle Sol", # for "Death Rite Bird"
  'Southeast Mountaintops': "Flame Peak", # for "Fire Giant"
  'Southwest Mountaintops': "Consecrated Snowfield", # for "Night's Cavalry"
  'Mountaintops of the Giants - North of Minor Erdtree': 'Consecrated Snowfield', # for "Putrid Avatar" at 60_50_57

  'Finger Ruins': "Fingerstone Hill", # for "Fallingstar Beast" at 61_52_48
}
npc_map = {
  'Hoarah Loux': 'Hoarah Loux, Warrior',
  'Loretta, Royal Knight': 'Royal Knight Loretta',
  'Sir Gideon Ofnir': 'Sir Gideon Ofnir, the All-Knowing',
  'Dragonkin Soldier of Nokron': 'Dragonkin Soldier',
  'Godrick the Reskinned': 'Godrick the Grafted',
  'Demi-Human Queen': 'Demi-Human Queen Gilika', # the other 3 "Demi-Human Queen" are all named (Margot, Marigga, Maggie), this one is at "Altus Plateau - Erdtree-Gazing Hill- Lux Ruins"
  'Ancient Dragon': 'Ancient Dragon Lansseax', # Lansseax has 2 stage, this one is at "Altus Plateau - Altus Tunnel Entrance", (Florissax is not a boss)
  'Dragonkin Soldier (Lake of Rot)': 'Dragonkin Soldier',
  'Jori, the Elder Inquisitor': 'Jori, Elder Inquisitor',
  'Tree Sentinel - Torch': 'Tree Sentinel',
  'Abductor Virgin': 'Abductor Virgin (Swinging Sickle)', # TODO: remove "()"" for these "s", another is "Abductor Virgin (Wheel)"
  'Ulcerated Tree Sprit': 'Ulcerated Tree Spirit', # note: "Spirit" misspelled
  'Battlenage': 'Battlemage Hugues', # note: "battlemage" misspelled
  'Nox Swordress & Nok Monk': 'Nox Monk', # note: "Nox Swordstress" misspelled
  # "Crucible Illusion"
}
def new_search(df_msg: pl.DataFrame, *, id_col = 'id', name_col = 'text_engus', query_fn = None, mapping = None):
  df_msg = df_msg.with_columns(
    normalized_name = pl.col(name_col).str.replace_all("'s ", '').str.replace_all('-', '').str.replace_all(',', '').str.replace_all(' ', '').str.to_lowercase()
  )
  def normalize(s: str):
    return s.replace("'s ", '').replace('-', '').replace(',', '').replace(' ', '').lower()
  def _search_normalized(name: str):
    df1 = df_msg.filter(pl.col(name_col) == name)
    if not df1.is_empty(): return df1
    df1 = df_msg.filter(pl.col('normalized_name') == normalize(name))
    return df1
  def _search(name: str):
    if query_fn is not None:
      query_names = query_fn(name)
    else:
      query_names = query_mapping(name, mapping=mapping)
    # print(query_names)
    for name in query_names:
      df1 = _search_normalized(name)
      if not df1.is_empty():
        return df1[0, id_col]
  return _search

def query_mapping(name: str, mapping: dict[str, str]) -> list[str]:
  if name is None or name == '': return []
  result = [name]
  if mapping is not None and name in mapping:
    result.append(mapping[name])
    return result
  return result

def query_place_name(name: str, *, mapping = place_map) -> list[str]:
  result = query_mapping(name, mapping)
  if len(result) > 1: return result
  if ' - ' in name:
    name1, name2 = name.split(' - ', 1)
    if name2 != "Minor Erdtree":
      result.extend(query_place_name(name2, mapping=mapping))
    result.extend(query_place_name(name1, mapping=mapping))
  suffix = [' Entrance', ' Midway']
  for s in suffix:
    if name.endswith(s):
      name2 = name.removesuffix(s)
      result.extend(query_place_name(name2, mapping=mapping))
  return result

def query_npc_name(name: str, *, mapping = npc_map) -> list[str]:
  result = query_mapping(name, mapping)
  if len(result) > 1: return result
  suffix = ['s', ' (Solo)', " (Duo)"]
  for s in suffix:
    if name.endswith(s):
      name2 = name.removesuffix(s)
      result.extend(query_place_name(name2, mapping=mapping))
  return result

def gen_boss(stage_dir: PathLike = stage2_dir):
  df = pl.read_csv(f"{stage_dir}/param/gameparam/GameAreaParam.csv")
  df_name = pl.DataFrame(read_paramdex_names("GameAreaParam")).rename(dict(id='id', name='row_name'))
  df = df.select('id').join(df_name, on='id', how='left').join(df, on='id', how='left').select(
    id = 'id',
    row_name = 'row_name',
    eventflag_id = 'defeatBossFlagId',
    map_efid = pl.concat_str(pl.col('bossMapAreaNo','bossMapBlockNo','bossMapMapNo').cast(pl.String).str.pad_start(2, '0'), separator='_'),
    pos_x = 'bossPosX',
    pos_y = 'bossPosY',
    pos_z = 'bossPosZ',
  )

  df = (df
    .with_columns(__tmp_split = pl.col('row_name').str.strip_prefix('[').str.split_exact('] ', 1))
    .unnest('__tmp_split').rename(dict(field_0='map_name', field_1='npc_name'))
    .with_columns(
      map_text_id = pl.col('map_name').map_elements(new_search(msg_all['PlaceName'], mapping=place_map, query_fn=query_place_name), return_dtype=pl.Int64),
    )
    .with_columns(
      npc_text_id = pl.col('npc_name').map_elements(new_search(msg_all['NpcName'], mapping=npc_map, query_fn=query_npc_name), return_dtype=pl.Int64),
    )
    .join(msg_all['NpcName'], left_on='npc_text_id', right_on='id', how='left').rename(msg_rename_with_prefix('name'))
    .join(msg_all['PlaceName'].drop('tag', 'dlc'), left_on='map_text_id', right_on='id', how='left').rename(msg_rename_with_prefix('mapname'))
    .with_columns(
      name_engus = pl.coalesce(pl.col('name_engus'), pl.col('npc_name')),
    )
  )
  dfr__game_area__unknown_map_name = df.filter((pl.col('map_name').is_not_null()) &(pl.col("map_name")!="")&(pl.col('map_text_id').is_null())).unique(['map_name', 'npc_name'])
  dfr__game_area__unknown_npc_name = df.filter((pl.col('npc_name').is_not_null()) &(pl.col("npc_name")!="")&(pl.col('npc_text_id').is_null())).unique('npc_name')
  for row in dfr__game_area__unknown_map_name.rows():
    logger.warning(f"[gen_boss] Unknown map_name: {row}")
  for row in dfr__game_area__unknown_npc_name.rows():
    logger.warning(f"[gen_boss] Unknown npc_name: {row}")
  return df.drop('row_name', 'map_name', 'npc_name')

df_boss = gen_boss(stage2_dir)
df_boss.write_csv(f"{ASSET_DIR}/boss.csv", quote_style='non_numeric')

# %% Generate weapon.csv
def pack_weapon_icons(src_dir: PathLike, dst_dir: PathLike, icon_ids: list[int], force = False, progress=True) -> list[str]:
  # from PIL import Image
  import imageio.v3 as imageio

  if progress:
    import tqdm
    bar = tqdm.tqdm(total=len(icon_ids), desc="weapon icons")
  files = {}
  for icon_id in icon_ids:
    icon_file = f"{src_dir}/MENU_Knowledge_{icon_id:05d}.dds"
    target_file = f"{dst_dir}/icon_{icon_id:05d}.png"
    if not force and Path(target_file).exists():
      files[icon_id] = target_file
      if progress: bar.update()
      continue
    try:
      img = imageio.imread(icon_file)
      imageio.imwrite(target_file, img)
      files[icon_id] = target_file
    except Exception as e:
      logger.error(f"[weapon_icon] Change format failed {icon_file} -> {target_file} error : {e}")
      continue
    if progress: bar.update()
    logger.info(f"[weapon_icon] Change format {icon_file} -> {target_file}")
  return files

def gen_weapon(stage_dir: PathLike, *, langs = langs, icon_path: PathLike = None):
  df_msg = load_mesaages(['WeaponName'], stage_dir=stage_dir)
  EquipParamWeapon = pl.read_csv(f"{stage_dir}/param/gameparam/EquipParamWeapon.csv").select(
    id = 'id', icon_id='iconId', type='wepType',
  )
  df = EquipParamWeapon.join(
    df_msg.df, on='id', how='left').rename(msg_rename_with_prefix('name', langs))
  if icon_path is not None:
    icon_ids = df['icon_id'].unique().to_list()
    Path(icon_path).mkdir(parents=True, exist_ok=True)
    files = pack_weapon_icons(f"{stage_dir}/menu/hi/00_solo", icon_path, icon_ids)
    df_files = pl.DataFrame(list(files.items()), schema={'icon_id': pl.Int64, 'path': pl.String}, orient='row')
    df = df.join(df_files, on='icon_id', how='left', )
  return df
df_weapon = gen_weapon(stage2_dir, icon_path=f"{ASSET_DIR}/icons").with_columns(path = pl.col("path").str.strip_prefix(ASSET_DIR+"/"))
df_weapon.write_csv(f"{ASSET_DIR}/weapon.csv", quote_style='non_numeric')

# %%
def find_in_msg(d, lang = None):
  if type(d) is str:
    if lang is None:
      return df_msg_all.filter(
        pl.any_horizontal(pl.col(pl.String).exclude('tag', 'dlc').str.contains(d))
      )
    return df_msg_all.filter(
      pl.col(f'text_{lang}').str.contains(str(d))
    )
  elif type(d) is int:
    return df_msg_all.filter(
      pl.col('id') == d
    )

def find_in_param(s, src_dir: PathLike = stage2_dir):
  s = str(s)
  path = Path(src_dir).joinpath("param/gameparam")
  for file in path.glob('*.csv'):
    with open(file, encoding='utf-8') as f:
      csvreader = csv.DictReader(f, delimiter=',')
      for row in csvreader:
        for k, v in row.items():
          if str(v) == s:
            print(file, row)
  print('done')


# find_in_msg("Adan, Thief of Fire")
# find_in_param(523000000)
# find_in_msg(241410)
# find_in_msg(903350313)
# 135600
# find_in_param(63002)

# %%
class Param:
  def __init__(self, name: str, *, stage_dir = stage2_dir):
    self.name = name
    df = pl.read_csv(stage_dir / f"param/gameparam/{name}.csv")
    self.names = read_paramdex_names(name)
    df_name = pl.DataFrame(self.names).rename(dict(id='id', name='row_name'))
    self.df = df.select('id').join(df_name, on='id', how='left').join(df, on='id', how='left')
    globals()[f"param__{name}__df"] = self.df

  def __str__(self) -> str:
    return f"Param({self.name}: {self.df})"

  def __repr__(self) -> str:
    return f"Param({self.name}: {self.df.shape})"

param__game_area = Param('GameAreaParam')
param__play_region = Param('PlayRegionParam')

param__area1 = Param('BonfireWarpParam')
param__area2 = Param('BonfireWarpSubCategoryParam')
param__area3 = Param('BonfireWarpTabParam')

param__sign_puddle = Param('SignPuddleParam')
param__sign_puddle1 = Param('SignPuddleSubCategoryParam')
param__sign_puddle2 = Param('SignPuddleTabParam')

# %%
df_wrap = (
  param__area1.df.select(
    id = 'id',
    row_name = 'row_name',
    # area_id = 'matchAreaId',
    area_sub_id = 'bonfireSubCategoryId',
    map_efid = pl.concat_str(pl.col('areaNo', 'gridXNo', 'gridZNo').cast(pl.String).str.pad_start(2, '0'), separator='_'),
    text_id = 'textId1',
  )
  .join(msg_all['PlaceName'], left_on='text_id', right_on='id', how='left').drop('tag', 'dlc', 'text_jpnjp', 'text_engus').rename(msg_rename_with_prefix('name'))
  .join(param__sign_puddle1.df.select(area_sub_id='id', area_sub_text_id='signPuddleCategoryText', area_tab_id = 'signPuddleTabId'), on='area_sub_id', how='left')
  .join(msg_all['GR_MenuText'], left_on='area_sub_text_id', right_on='id', how='left').drop('tag', 'dlc', 'text_jpnjp', 'text_engus').rename(msg_rename_with_prefix('area_name'))
  .join(param__sign_puddle2.df.select(area_tab_id='id', dlc='isDlcTab', area_tab_text_id='tabTextId'), on='area_tab_id', how='left')
  .join(msg_all['GR_MenuText'], left_on='area_tab_text_id', right_on='id', how='left').drop('tag', 'dlc_right', 'text_jpnjp', 'text_engus').rename(msg_rename_with_prefix('tab_name'))
)
df_wrap

# %%
df_puddle = (
  param__sign_puddle.df.select(
    id = 'id',
    row_name = 'row_name',
    area_id = 'matchAreaId',
    area_sub_id = 'signSubCategoryId',
    map_efid = pl.concat_str(pl.col('areaNo', 'gridXNo', 'gridZNo').cast(pl.String).str.pad_start(2, '0'), separator='_'),
    text_id = 'locationTextId',
  )
  .join(msg_all['PlaceName'], left_on='text_id', right_on='id', how='left').drop('tag', 'dlc', 'text_jpnjp', 'text_engus').rename(msg_rename_with_prefix('name'))
  .join(param__sign_puddle1.df.select(area_sub_id='id', area_sub_text_id='signPuddleCategoryText', area_tab_id = 'signPuddleTabId'), on='area_sub_id', how='left')
  .join(msg_all['GR_MenuText'], left_on='area_sub_text_id', right_on='id', how='left').drop('tag', 'dlc', 'text_jpnjp', 'text_engus').rename(msg_rename_with_prefix('area_name'))
  .join(param__sign_puddle2.df.select(area_tab_id='id', dlc='isDlcTab', area_tab_text_id='tabTextId'), on='area_tab_id', how='left')
  .join(msg_all['GR_MenuText'], left_on='area_tab_text_id', right_on='id', how='left').drop('tag', 'dlc_right', 'text_jpnjp', 'text_engus').rename(msg_rename_with_prefix('tab_name'))
)
df_puddle

# %%
df_puddle.group_by('map_efid', 'area_sub_id').len().group_by('map_efid').len().sort('len')

# %%
"""
consider these 2 lines:
`12030390,[Deeproot Depths],"Crucible Knight",12020390,`
`30100801,"[Auriza Hero's Grave] Crucible Knight",30100800,"[Auriza Hero's Grave] Crucible Knight Ordovis"`
in boss.csv, only 12030390 present, and 30100800/30100801 combines to 30100800
"""
dfr__game_area__id_not_equal_defeatbossflagid = (
param__game_area.df.filter(pl.col("id") != pl.col("defeatBossFlagId"))
  .join(param__game_area.df, left_on="defeatBossFlagId", right_on="id", suffix="_flag", how="left")
  .select("id", "row_name", "defeatBossFlagId", "row_name_flag")
)
dfr__game_area__id_not_equal_defeatbossflagid
