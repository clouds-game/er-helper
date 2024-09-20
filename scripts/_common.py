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

# %%
