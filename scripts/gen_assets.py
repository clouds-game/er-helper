# %%
import csv
import json
from _common import *
import polars as pl
import pathlib

logger = get_logger(__name__, filename=f'logs/gen_assets_{today_str()}.log')

config = load_config()
game_dir = config['unpack']['src_dir']
dst_dir = config['unpack']['stage2_dir']

ASSET_DIR = "tauri-app/src-tauri/assets"
langs = ['zhocn', 'jpnjp', 'engus']
# %%

def get_names(filenames):
  names = {}
  for lang in langs:
    # df = pl.DataFrame(schema={'id': pl.Int64, 'text': pl.String})
    dfs = []
    for filename in filenames:
      msg_path = pathlib.Path(dst_dir).joinpath(f"msg/{lang}/{filename}")
      dfs.append(pl.read_json(msg_path))
      # dfs.append(pl.read_json(msg_path).with_columns(textstrip=pl.col('text').str.strip_chars()))
    df = pl.concat(dfs)
    names[lang] = df
  return names


def pack_grace():
  place_names = get_names(['PlaceName.json', 'PlaceName_dlc01.json'])
  menutext_names = get_names(['GR_MenuText.json', 'GR_MenuText_dlc01.json'])

  BonfireWarpParam_path = f"{dst_dir}/param/gameparam/BonfireWarpParam.csv"
  BonfireWarpSubCategoryParam_path = f"{
      dst_dir}/param/gameparam/BonfireWarpSubCategoryParam.csv"
  BonfireWarpParam = pl.read_csv(BonfireWarpParam_path).select(pl.col(['id', 'eventflagId', 'bonfireSubCategoryId']),
                                                               pl.col('textId1').alias('textId'))
  BonfireWarpSubCategoryParam = pl.read_csv(BonfireWarpSubCategoryParam_path).select(
      pl.col('id'), pl.col('textId').alias('mapId'))
  df = BonfireWarpParam.join(
      BonfireWarpSubCategoryParam, left_on='bonfireSubCategoryId', right_on='id')
  for lang in langs:
    df = df.join(place_names[lang], left_on='textId', right_on='id', how='left').rename(
        {'text': f'name_{lang}'})
    df = df.join(menutext_names[lang], left_on='mapId', right_on='id', how='left').rename(
        {'text': f'mapname_{lang}'})
  df.write_json(f"grace.out.json")
# %%


def pack_boss():
  pass

# %%


def pack_weapon():
  weapon_names = (pl.concat([pl.read_json(f"{dst_dir}/msg/zhocn/{filename}.json") for filename in ["WeaponName", "WeaponName_dlc01"]])
                  .filter([pl.col('text').is_not_null(), pl.col('text') != '[ERROR]']))
  EquipParamWeapon = (pl.read_csv(f"{dst_dir}/param/gameparam/EquipParamWeapon.csv").select(['id', 'iconId', 'wepType'])
                      .rename({'iconId': 'icon_id', 'wepType': 'wep_type'}))
  df = EquipParamWeapon.join(
      weapon_names, left_on='id', right_on='id').rename({'text': "name"})
  df.write_json(f"{ASSET_DIR}/weapon.out.json")
  icon_ids = [row['icon_id'] for row in df.iter_rows(named=True)]
  icon_ids = list(set(icon_ids))
  return icon_ids


def pack_weapon_icons(icon_ids: list[int], progress=True):
  from PIL import Image
  import imageio.v2 as imageio
  icons_src_dir = pathlib.Path(f"{dst_dir}/menu/hi/00_solo")
  icons_dst_dir = pathlib.Path(f"{ASSET_DIR}/icons")

  icon_ids = list(set(icon_ids))
  if progress:
    import tqdm
    bar = tqdm.tqdm(total=len(icon_ids), desc="change format")
  for icon_id in icon_ids:
    icon_file = icons_src_dir.joinpath(f"MENU_Knowledge_{icon_id:05d}.dds")
    target_file = icons_dst_dir.joinpath(icon_file.stem).with_suffix('.png')
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

icon_ids = pack_weapon()
pack_weapon_icons(icon_ids)

# %%
import pathlib

def find_in_msg(d, lang = 'engus'):
  path = pathlib.Path(dst_dir).joinpath(f"msg/{lang}")
  name = 'id' if isinstance(d, int) else 'text'
  for file in path.glob('*.json'):
    with open(file, encoding='utf-8') as f:
      data = json.load(f)
      for x in data:
        if d == x[name]:
          print(file, x)
  print('done')


def find_in_param(s):
  s = str(s)
  path = pathlib.Path(dst_dir).joinpath("param/gameparam")
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
path = pathlib.Path(dst_dir).joinpath("param/gameparam/GameAreaParam.csv")
df = pl.read_csv(path).select(pl.col(['id', 'defeatBossFlagId', 'bossMapAreaNo', 'bossMapBlockNo',
                                      'bossMapMapNo', 'displayAimFlagId', 'bossChallengeFlagId', 'notFindBossTextId']))
df

# %%
path = f"{dst_dir}/param/gameparam/NpcParam.csv"
df1 = pl.read_csv(path)
df2 = pl.concat(pl.read_json(f'{dst_dir}/msg/zhocn/{i}.json') for i in ['NpcName', 'NpcName_dlc01'])
dfx = df1.join(df2, left_on='nameId', right_on='id').unique('nameId').select(pl.col(['nameId', 'text']))
# %%
import polars as pl
path = f"{dst_dir}/param/gameparam/GameAreaParam.csv"
df = (pl.read_csv(path).select(['id','defeatBossFlagId'])

)
df2 = (pl.read_csv("tauri-app/src-tauri/assets/boss.csv")
)

df2 = df2.join(df, left_on='id', right_on='defeatBossFlagId', how='left')
# df2 = df2.filter(pl.col('id').is_null())
df2 = df2.group_by('id').all()
df2
# %%

import polars as pl

df = (pl.read_csv(f"{dst_dir}/param/gameparam/NpcParam.csv")
      .select(['id', 'nameId', 'npcType','teamType', 'moveType', 'vowType','toughness', 'roleNameId', 'loadAssetId', 'behaviorVariationId'])
      )
df = df.filter(pl.col('npcType') == 1)


df

# %%
