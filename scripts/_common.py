# %%
import os

def enter_project_root():
  while not os.path.exists('pixi.toml'):
    os.chdir('..')
