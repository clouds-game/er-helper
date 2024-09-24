import pathlib


path_roots = [
    pathlib.Path("N:/GR/data/INTERROOT_win64/"),
]

NameMaps = {
  "AssetEnvironmentGeometryParam": "AssetGeometryParam",
  "ChrEquipModelParam": "ChrModelParam",
  "CutsceneWeatherOverrideGparamConvertParam": "CutsceneWeatherOverrideGparamIdConvertParam",
  "HPEstusFlaskRecoveryParam": "EstusFlaskRecoveryParam",
  "MapGridCreateHeightDetailLimitInfo": "",
  "MenuColorTableParam": "MenuParamColorTable",
  "MenuValueTableParam": "MenuValueTableSpecParam",
  "MPEstusFlaskRecoveryParam": "EstusFlaskRecoveryParam",
  "MultiHPEstusFlaskBonusParam": "MultiEstusFlaskBonusParam",
  "MultiMPEstusFlaskBonusParam": "MultiEstusFlaskBonusParam",
  "SignPuddleSubCategoryParam": "SignPuddleParam",
  "SignPuddleTabParam": "SignPuddleParam",
  "SpeedtreeParam": "SpeedtreeModel",
  "WwiseValueToStrParam_BgmBossChrIdConv": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_EnvPlaceType": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_AttackStrength": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_AttackType": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_DamageAmount": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_DeffensiveMaterial": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_GrassHitType": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_HitStop": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_OffensiveMaterial": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_PlayerEquipmentBottoms": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_PlayerEquipmentTops": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_PlayerShoes": "WwiseValueToStrConvertParamFormat",
  "WwiseValueToStrParam_Switch_PlayerVoiceType": "WwiseValueToStrConvertParamFormat",
  }


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
    import clr
    import System
    return obj.GetType().GetElementType() == clr.GetClrType(System.Byte)
  except:
    return False


def get_format(byte_array: bytes):
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
  return res.strip()


def get_def_name(name: str, exist_names: list[str]):
  if name in exist_names:
    return name
  if name.removesuffix("Param") in exist_names:
    return name.removesuffix("Param")
  if name + "Param" in exist_names:
    return name + "Param"
  if name.rsplit("_", 1)[0] in exist_names:
    return name.rsplit("_", 1)[0]
  return NameMaps.get(name, name)


def read_csharp_bytes(path: pathlib.Path):
  import clr
  import System
  with open(path, "rb") as f:
    file_bytes = f.read()
  csharp_bytes = System.Array[System.Byte](file_bytes)
  return csharp_bytes
