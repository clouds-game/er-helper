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
def get_names(filenames: list[str]):
  names = {}
  for lang in langs:
    # df = pl.DataFrame(schema={'id': pl.Int64, 'text': pl.String})
    dfs = []
    for filename in filenames:
      msg_path = Path(stage2_dir).joinpath(f"msg/{lang}/{filename}")
      dfs.append(pl.read_json(msg_path))
      # dfs.append(pl.read_json(msg_path).with_columns(textstrip=pl.col('text').str.strip_chars()))
    df = pl.concat(dfs)
    names[lang] = df
  return names

def gen_grace(target_path: PathLike, src_dir: PathLike):
  place_names = get_names(['PlaceName.json', 'PlaceName_dlc01.json'])
  menutext_names = get_names(['GR_MenuText.json', 'GR_MenuText_dlc01.json'])

  BonfireWarpParam_path = f"{src_dir}/param/gameparam/BonfireWarpParam.csv"
  BonfireWarpSubCategoryParam_path = f"{src_dir}/param/gameparam/BonfireWarpSubCategoryParam.csv"
  BonfireWarpParam = pl.read_csv(BonfireWarpParam_path).select(
    pl.col(['id', 'eventflagId', 'bonfireSubCategoryId']),
    pl.col('textId1').alias('textId')
  )
  BonfireWarpSubCategoryParam = pl.read_csv(BonfireWarpSubCategoryParam_path).select(
      pl.col('id'), pl.col('textId').alias('mapId'))
  df = BonfireWarpParam.join(
      BonfireWarpSubCategoryParam, left_on='bonfireSubCategoryId', right_on='id')
  for lang in langs:
    df = df.join(place_names[lang], left_on='textId', right_on='id', how='left').rename(
        {'text': f'name_{lang}'})
    df = df.join(menutext_names[lang], left_on='mapId', right_on='id', how='left').rename(
        {'text': f'mapname_{lang}'})
  df.write_json(target_path)
gen_grace(f"grace.out.json", stage2_dir)

# %%
def pack_boss():
  pass

def pack_weapon(target_path: PathLike, src_dir: PathLike):
  weapon_names = (pl.concat([pl.read_json(f"{src_dir}/msg/zhocn/{filename}.json") for filename in ["WeaponName", "WeaponName_dlc01"]])
                  .filter([pl.col('text').is_not_null(), pl.col('text') != '[ERROR]']))
  EquipParamWeapon = (pl.read_csv(f"{src_dir}/param/gameparam/EquipParamWeapon.csv").select(['id', 'iconId', 'wepType'])
                      .rename({'iconId': 'icon_id', 'wepType': 'wep_type'}))
  df = EquipParamWeapon.join(
      weapon_names, left_on='id', right_on='id').rename({'text': "name"})
  df.write_json(target_path)
  icon_ids = [row['icon_id'] for row in df.iter_rows(named=True)]
  icon_ids = list(set(icon_ids))
  return icon_ids


def pack_weapon_icons(src_dir: Path, dst_dir: Path,icon_ids: list[int], progress=True):
  from PIL import Image
  import imageio.v2 as imageio

  icon_ids = list(set(icon_ids))
  if progress:
    import tqdm
    bar = tqdm.tqdm(total=len(icon_ids), desc="change format")
  for icon_id in icon_ids:
    icon_file = src_dir.joinpath(f"MENU_Knowledge_{icon_id:05d}.dds")
    target_file = dst_dir.joinpath(icon_file.stem).with_suffix('.png')
    try:
      image_array = imageio.imread(icon_file)
      image = Image.fromarray(image_array)
      image.save(target_file)
    except Exception as e:
      logger.error(f"[ weapon_icon ] Change format failed {icon_file} -> {target_file} error : {e}")
      continue
    if progress:
      bar.update()
    logger.info(f"[ weapon_icon ] Change format {icon_file} -> {target_file}")

icon_ids = pack_weapon(f"{ASSET_DIR}/weapon.out.json", stage2_dir)
pack_weapon_icons(Path(f"{stage2_dir}/menu/hi/00_solo"), Path(f"{ASSET_DIR}/icons"), icon_ids)


# %%
def find_in_msg(d, lang = 'engus', src_dir: PathLike = stage2_dir):
  path = Path(src_dir).joinpath(f"msg/{lang}")
  name = 'id' if isinstance(d, int) else 'text'
  for file in path.glob('*.json'):
    with open(file, encoding='utf-8') as f:
      data = json.load(f)
      for x in data:
        if d == x[name]:
          print(file, x)
  print('done')


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
find_in_msg(34010000, 'zhocn')
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
class Message:
  def __init__(self, df: pl.DataFrame, *, name: str, dlc_part: str = None):
    self.df = df
    self.name = name
    self.dlc_part = dlc_part

  @staticmethod
  def load(name: str, *, langs = langs, stage_dir = stage2_dir):
    dlc_part = name.rsplit('_', 1)[-1]
    if dlc_part.startswith('dlc'):
      name = name.removesuffix('_' + dlc_part)
    else:
      dlc_part = None
    data: dict[str, list] = {}
    for lang in langs:
      path = Path(stage_dir).joinpath(f"msg/{lang}/{name}.json")
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

msg__npc_name = Message.load('NpcName')
msg__npc_name.df

messages = [Message.load(path.stem)
  for path in stage2_dir.joinpath('msg/jpnjp').glob('*.json')]
msg_all = Message(pl.concat([msg.df for msg in messages]), name='all')
df_msg_all = msg_all.df
df_msg_all

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
