from os import PathLike
from pathlib import Path

path_roots = [
  "N:\\GR\\data\\INTERROOT_win64\\",
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


def UnrootBNDPath(path: PathLike) -> tuple[str, str | None]:
  path = str(path)
  for root in path_roots:
    if path.startswith(root):
      return (path.removeprefix(root), root)
  return (path, None)


def is_csharp_byte_array(obj):
  try:
    import clr
    import System
    return obj.GetType().GetElementType() == clr.GetClrType(System.Byte)
  except:
    return False

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

def hash_path(path: PathLike, prefix: str = None) -> str:
  import hashlib
  data = Path(path).as_posix().lower().encode('utf-8')
  if prefix is not None:
    data = prefix.encode('utf-8') + b'::' + data
  return hashlib.sha256(data).hexdigest()