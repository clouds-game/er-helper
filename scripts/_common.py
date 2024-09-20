# %%
import os
import logging

def enter_project_root():
  while not os.path.exists('pixi.toml'):
    os.chdir('..')

def get_logger(name: str, *, level: int = logging.INFO, filename: str | None = None) -> logging.Logger:
  logger = logging.getLogger(name)
  logger.setLevel(level)

  if filename is not None:
    import pathlib
    pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)
    ch = logging.FileHandler(filename, mode='a')
  else:
    ch = logging.StreamHandler()
  ch.setLevel(level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  ch.setFormatter(formatter)
  logger.addHandler(ch)
  return logger

def today_str() -> str:
  import datetime
  return str(datetime.date.today()).replace('-', '')

def load_config() -> dict:
  import tomllib, pathlib
  origin_curdir = curdir = pathlib.Path(".").absolute()

  while not os.path.exists(curdir / 'config.toml'):
    if os.path.exists('pixi.toml') or os.path.exists('config.example.toml') or curdir.absolute() == curdir.parent.absolute():
      print(f"config.toml not found (from {origin_curdir} to {curdir})")
      return None
    curdir = curdir.parent
  with open(curdir / "config.toml", "rb") as f:
    return tomllib.load(f)

# %%
from dataclasses import dataclass
@dataclass
class NetField:
  name: str
  type: str
  collectable: bool
  static: bool
  public: bool
  can_read: bool
  can_write: bool

  @staticmethod
  def from_field(f):
    return NetField(
      name=f.Name,
      type=f.FieldType.Name,
      collectable=f.IsCollectible,
      static=f.IsStatic,
      public=f.IsPublic,
      can_read=True,
      can_write=True,
    )
  @staticmethod
  def from_property(p):
    return NetField(
      name=p.Name,
      type=p.PropertyType.Name,
      collectable=p.CanRead,
      static=p.GetGetMethod().IsStatic,
      public=p.GetGetMethod().IsPublic,
      can_read=p.CanRead,
      can_write=p.CanWrite,
    )

  @staticmethod
  def collect_type(ty):
    return [NetField.from_field(i) for i in ty.GetFields()] + [NetField.from_property(i) for i in ty.GetProperties()]

  @staticmethod
  def to_dict(fields: list["NetField"], instance):
    return {f.name: getattr(instance, f.name) for f in fields}
