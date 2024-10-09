import os
from pathlib import Path

cwd = Path(os.getcwd()).as_posix()

print(f"Current working directory: {cwd}")

with open("python.env.in", "r") as f:
  env = f.read()
  env = env.replace("${PWD}", cwd)

with open("python.env", "w") as f:
  f.write(env)
