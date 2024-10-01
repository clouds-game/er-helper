# %%
import csv
from _common import *

logger = get_logger(__name__, filename=f'logs/gen_assets_{today_str()}.log')

config = load_config()
game_dir = config['unpack']['src_dir']
stage1_dir = config['unpack']['stage1_dir']
stage2_dir = Path(config['unpack']['stage2_dir'])

ASSET_DIR = "tauri-app/src-tauri/assets"
paramdex_dir = Path("vendor/WitchyBND/WitchyBND/Assets/Paramdex/ER")
langs = ['zhocn', 'jpnjp', 'engus']

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

def msg_rename_prefix_dict(prefix: str, langs = langs):
  return {f'text_{lang}': f'{prefix}_{lang}' for lang in langs}

# msg__npc_name = Message.load('NpcName')
# msg__npc_name.df

def load_mesaages(name_list: list[str] = None, *, stage_dir = stage2_dir, langs=langs, dlc = True) -> Message:
  if name_list is None:
    name_list = [path.stem for path in stage_dir.joinpath('msg/jpnjp').glob('*.json')]
  elif dlc:
    name_list = [f"{name}{dlc}" for name in name_list for dlc in ['', '_dlc01', '_dlc02']]
  messages = [Message.load(name, langs=langs) for name in name_list]
  return Message(pl.concat([msg.df for msg in messages]), name=f'all[{len(name_list)}]')

df_msg_all = load_mesaages().df

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
    msg_rename_prefix_dict('name', langs)
  )
  df = df.join(df_msg['GR_MenuText'].select('id', *langs_col), left_on='map_text_id', right_on='id', suffix="_mapname", how='left').rename(
    msg_rename_prefix_dict('mapname', langs)
  )
  assert(df.shape[0] == BonfireWarpParam.shape[0])
  return df
df_grace = gen_grace(stage2_dir)
df_grace.write_csv(f"{ASSET_DIR}/graces.csv", quote_style='non_numeric')

# %%
def gen_boss():
  pass

# %%
def pack_weapon_icons(src_dir: PathLike, dst_dir: PathLike, icon_ids: list[int], force = False, progress=True) -> list[str]:
  # from PIL import Image
  import imageio.v3 as imageio

  if progress:
    import tqdm
    bar = tqdm.tqdm(total=len(icon_ids), desc="weapon icons")
  files = {}
  for icon_id in icon_ids:
    icon_file = f"{src_dir}/MENU_Knowledge_{icon_id:05d}.dds"
    target_file = f"{dst_dir}/icons_{icon_id:05d}.png"
    if not force and Path(target_file).exists():
      files[icon_id] = target_file
      if progress: bar.update()
      continue
    try:
      img = imageio.imread(icon_file)
      imageio.imwrite(target_file, img)
      files[icon_id] = target_file
    except Exception as e:
      logger.error(f"[ weapon_icon ] Change format failed {icon_file} -> {target_file} error : {e}")
      continue
    if progress: bar.update()
    logger.info(f"[ weapon_icon ] Change format {icon_file} -> {target_file}")
  return files

def gen_weapon(stage_dir: PathLike, *, langs = langs, icon_path: PathLike = None):
  df_msg = load_mesaages(['WeaponName'], stage_dir=stage_dir)
  EquipParamWeapon = pl.read_csv(f"{stage_dir}/param/gameparam/EquipParamWeapon.csv").select(
    id = 'id', icon_id='iconId', type='wepType',
  )
  df = EquipParamWeapon.join(
    df_msg.df, on='id', how='left').rename(msg_rename_prefix_dict('name', langs))
  if icon_path is not None:
    icon_ids = df['icon_id'].unique().to_list()
    Path(icon_path).mkdir(parents=True, exist_ok=True)
    files = pack_weapon_icons(f"{stage_dir}/menu/hi/00_solo", icon_path, icon_ids)
    df_files = pl.DataFrame(list(files.items()), schema={'icon_id': pl.Int64, 'path': pl.String}, orient='row')
    df = df.join(df_files, on='icon_id', how='left', )
  return df
df_weapon = gen_weapon(stage2_dir, icon_path=f"{ASSET_DIR}/icons")
df_weapon.with_columns(path = pl.col("path").str.strip_prefix(ASSET_DIR+"/")).write_csv(f"{ASSET_DIR}/weapons.csv", quote_style='non_numeric')

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
find_in_msg(34010000)
# find_in_msg(903350313)
# 135600
# find_in_param(36602338)
# %%
df = pl.read_csv(stage2_dir / "param/gameparam/GameAreaParam.csv").select(
  'id', 'defeatBossFlagId', 'bossMapAreaNo', 'bossMapBlockNo',
  'bossMapMapNo', 'displayAimFlagId', 'bossChallengeFlagId', 'notFindBossTextId',
)
df

# %%
df1 = pl.read_csv(stage2_dir / "param/gameparam/NpcParam.csv")
df2 = pl.concat(pl.read_json(f'{stage2_dir}/msg/zhocn/{i}.json') for i in ['NpcName', 'NpcName_dlc01'])
dfx = df1.join(df2, left_on='nameId', right_on='id').unique('nameId').select(pl.col(['nameId', 'text']))
# %%
df = (pl.read_csv(stage2_dir / "param/gameparam/GameAreaParam.csv")
  .select('id','defeatBossFlagId')
)
df2 = (pl.read_csv("tauri-app/src-tauri/assets/boss.csv")
  .join(df, left_on='id', right_on='defeatBossFlagId', how='left')
  # .filter(pl.col('id').is_null())
  .group_by('id').all()
)
df2

# %%

# %%
def search_row(df: pl.DataFrame, message: str) -> pl.DataFrame:
  import polars_distance as pld
  result = []
  for col in df.columns:
    if col.startswith('text_'):
      df_result = df.filter(pl.col(col).str.contains(message)).with_columns(
        distance = pl.lit(message),
        lang = pl.lit(col.removeprefix('text_')),
      ).with_columns(
        pld.col('distance').dist_str.hamming(pl.col(col))
      )
      result.append(df_result)
  return pl.concat(result).sort(
    'distance', descending=False, nulls_last=True
  )
search_row(df_msg_all, 'Banished Knight')

# %%
class Param:
  def __init__(self, name: str, *, stage_dir = stage2_dir):
    self.name = name
    df = pl.read_csv(stage_dir / f"param/gameparam/{name}.csv")
    self.names = self.read_names(name)
    df_name = pl.DataFrame(self.names).rename(dict(id='id', name='row_name'))
    self.df = df.select('id').join(df_name, on='id', how='left').join(df, on='id', how='left')
    globals()[f"param__{name}__df"] = self.df

  @staticmethod
  def read_names(name: str):
    with open(paramdex_dir / f"Names/{name}.txt") as f:
      lines = f.readlines()
    result: list[tuple[int, str]] = []
    for line in lines:
      id, name = line.split(' ', 1)
      result.append({'id': int(id), 'name': name})
    return result

  def __str__(self) -> str:
    return f"Param({self.name}: {self.df})"

  def __repr__(self) -> str:
    return f"Param({self.name}: {self.df.shape})"

param__game_area = Param('GameAreaParam')

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
# %%
search_row(df_msg_all, "Auriza Hero's Grave")

# %%
