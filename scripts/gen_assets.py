# %%
import csv
from _common import *

logger = get_logger(__name__, filename=f'logs/gen_assets_{today_str()}.log')

config = load_config()
stage2_dir = Path(config['unpack']['stage2_dir'])
langs = ['zhocn', 'jpnjp', 'engus']

# %%
def get_names(filenames: list[str], src_dir: PathLike) -> dict[str, pl.DataFrame]:
  names = {}
  for lang in langs:
    # df = pl.DataFrame(schema={'id': pl.Int64, 'text': pl.String})
    dfs = []
    for filename in filenames:
      msg_path = Path(src_dir).joinpath(f"msg/{lang}/{filename}")
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
find_in_param(523000000)
# find_in_msg(71500, 'zhocn')
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
df = (pl.read_csv(stage2_dir / "param/gameparam/NpcParam.csv")
  .select(['id', 'nameId', 'npcType','teamType', 'moveType', 'vowType','toughness', 'roleNameId', 'loadAssetId', 'behaviorVariationId'])
  .filter(pl.col('npcType') == 1)
)
df

# %%