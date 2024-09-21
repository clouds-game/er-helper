# %%
from _common import *

# enter_project_root()

ASSET_DIR = "tauri-app/src-tauri/assets"

# %%
def regex_format(template: str, **kwargs: dict[str, str]):
  for c in regex_format.to_escape:
    template = template.replace(c, f"\\{c}")
  template = regex_format.space_regex.sub(" ", template).replace(" ", r"\s*")
  template = regex_format.template_regex.sub(lambda m: f"(?P<{m.group('tag')}>{kwargs[m.group('tag')]})", template)
  return re.compile(template)
regex_format.to_escape = r". ^ $ * + ? { } [ ] \ | ( )".replace(" ", "")
regex_format.space_regex = re.compile(r"\s+")
regex_format.template_regex = re.compile(r"<\s*(?P<tag>[^>]+)\s*>")

def parse_rs(input: str, *,
  prelude_str: str | None = None, # "Lazy::new(|| {"
  epilogue_str: str | None = None, # "});"
  group_regex = re.compile(r"^// (?P<group_name>.*)$"),
  regex,
):
  result: dict[object] = []
  group_name: str | None = None
  start = prelude_str is None
  for line in input.splitlines():
    line = line.strip()
    if not start:
      if prelude_str in line:
        start = True
      continue
    if epilogue_str and epilogue_str in line:
      break
    r = group_regex.match(line)
    if r:
      group_name = r.group('group_name')
      continue
    r = regex.match(line)
    if r:
      result.append({'group_name': group_name} | r.groupdict())
  return pl.DataFrame(result)

# %%
if os.path.exists(f"{ASSET_DIR}/graces.in.rs") and not os.path.exists(f"{ASSET_DIR}/graces.csv"):
  with open(f"{ASSET_DIR}/graces.in.rs") as f:
    data = f.read()
  df = parse_rs(
    data,
    prelude_str="pub static GRACES: Lazy<Mutex<HashMap<Grace, (MapName, u32, &str)>>>",
    regex=regex_format("( Grace::<name>, (MapName::<map>, <id>, \"<desc>\" ) )",
      name=r"[a-zA-Z0-9_]+", map=r"[a-zA-Z0-9_]+", id=r"\d+", desc=r"[^\"]+"),
  )
  invalid_count = df.with_columns(
    gen_name = pl.col('desc').str.replace_all(r"[^a-zA-Z]", ""),
    gen_map = pl.col('group_name').str.replace_all(r"[^a-zA-Z]", ""),
  ).with_columns(
    valid_name = pl.col('gen_name').str.to_uppercase() == pl.col('name').str.to_uppercase(),
    valid_map = pl.col('gen_map').str.to_uppercase() == pl.col('map').str.to_uppercase(),
  ).filter(pl.col('valid_name').not_() | pl.col('valid_map').not_())
  print(invalid_count)
  df = df.select(
    id = pl.col('id').str.json_decode(pl.UInt32),
    map = 'group_name',
    name = 'desc',
  )
  df.write_csv(f"{ASSET_DIR}/graces.csv", quote_style="non_numeric")

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
print(df.group_by('block').len())
df.write_json(f"{ASSET_DIR}/graces.out.json")

# %%
if os.path.exists(f"{ASSET_DIR}/bosses.in.rs") and not os.path.exists(f"{ASSET_DIR}/boss.csv"):
  with open(f"{ASSET_DIR}/bosses.in.rs") as f:
    data = f.read()
  df = parse_rs(
    data,
    prelude_str="pub static BOSSES: Lazy<Mutex<HashMap<Boss, (u32,&str)>>>",
    regex=regex_format("( Boss::<name>, ( <id>, \"<desc>\" ) )",
      name=r"[a-zA-Z0-9_]+", id=r"\d+", desc=r"[^\"]+"),
  )
  invalid_count = df.with_columns(
    gen_name = pl.col('desc').str.replace_all(r"[^a-zA-Z]", ""),
  ).with_columns(
    valid_name = pl.col('gen_name').str.to_uppercase() == pl.col('name').str.to_uppercase(),
  ).filter(pl.col('valid_name').not_())
  print(invalid_count)
  df = df.select(
    id = pl.col('id').str.json_decode(pl.UInt32),
    map = 'group_name',
    name = 'desc',
  )
  df.write_csv(f"{ASSET_DIR}/boss.csv", quote_style="non_numeric")

# %%
df = pl.read_csv(f"{ASSET_DIR}/boss.csv")
df = df.with_columns(
  block = pl.col('id') // 1000,
  block_idx = pl.col('id') % 1000,
).join(df_bits.select(block='from', offset='to'), on='block').with_columns(
  id = pl.col('id').cast(pl.UInt32),
  offset = (pl.col('offset') * 125 + pl.col('block_idx') // 8).cast(pl.UInt32),
  bit_mask = pl.lit(2).pow((7 - pl.col('block_idx') % 8)).cast(pl.UInt8),
)
print(df.group_by('block').len())
df.write_json(f"{ASSET_DIR}/boss.out.json")

# %%
