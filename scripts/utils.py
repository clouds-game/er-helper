import pathlib

path_roots = [
    pathlib.Path("N:/GR/data/INTERROOT_win64/"),
]


def UnrootBNDPath(path: str):
  path = pathlib.Path(path)
  for root in path_roots:
    try:
      return (path.relative_to(root), root)
    except Exception as e:
      return (path, None)
  return (path, None)



def is_csharp_byte_array(obj):
  try:
    # todo
    return str(obj.GetType().GetElementType()) == "System.Byte"
  except:
    return False


def get_format(byte_array):
  res = ""
  for b in byte_array:
    try:
      c = chr(b)
      if c.isprintable():
        res += c
      else:
        break
    except:
      print(f"Failed to convert byte {b} to char")
      break
  return res
