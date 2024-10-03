# %%
from _common import *
import requests
import re
ASSET_DIR = "tauri-app/assets"
logger = get_logger(__name__, filename=f'logs/download_icons_{today_str()}.log')

def fetch_icon(id, name):
  if os.path.exists(f"{ASSET_DIR}/icons/icon_{id:05d}.png"):
    return
  url = f"https://wiki.biligame.com/eldenring/{name}"
  logger.info(f"Downloading {id} {name} {url}")
  resp = requests.get(url)
  if resp.status_code != 200:
    logger.warning(f"Download {id} failed {resp.status_code} {url} {resp}")
    return
  text = resp.text
  start = text.find(f'<img alt="{name}.png"')
  end = text.find('/>', start)
  img_text = text[start:end]
  groups = re.findall(r"https:[^ \"]*", img_text)
  if not groups:
    logger.warning(f"Image not found {id} {name} {img_text}")
    return
  img_url = groups[-1]
  print(id, name, img_url)
  resp = requests.get(img_url)
  if resp.status_code != 200:
    logger.warning(f"Download {id} failed {resp.status_code} {img_url} {resp}")
    return
  body = resp.content
  with open(f"{ASSET_DIR}/icons/icon_{id:05d}.png", 'wb') as f:
    f.write(body)
  logger.info(f"Downloaded {id} {name} {img_url}")
# %%
Path(f"{ASSET_DIR}/icons").mkdir(parents=True, exist_ok=True)
df = pl.read_csv(f"{ASSET_DIR}/weapon.csv")
for id, name in df.filter(pl.col('name_zhocn').is_not_null() & pl.col('name_zhocn').str.contains('[ERROR]|DLC dummy').not_()).unique('icon_id', keep='first', maintain_order=True).select('icon_id', 'name_zhocn').rows():
  fetch_icon(id, name)

# %%
df = pl.read_csv(f"{ASSET_DIR}/goods.csv")
for id, name in df.filter(pl.col('name_zhocn').is_not_null() & pl.col('name_zhocn').str.contains('[ERROR]|DLC dummy').not_()).filter(pl.col("type").is_in([5, 16, 17, 18])).unique('icon_id', keep='first', maintain_order=True).select('icon_id', 'name_zhocn').rows():
  fetch_icon(id, name)

# %%

# %%
