use crate::{db::WEAPON_MAP, sync::MyState, Result};
use er_save_lib::save::user_data_x::EquippedArmamentsAndItems;

#[derive(Default, Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct WeaponInfo {
  pub weapon_id: u32,
  pub level: u8,
  pub name: String,
  pub icon_id: u16,
  pub wep_type: u16,
}

impl WeaponInfo {
  pub fn new(weapon_id: &u32) -> Self {
    let level = weapon_id % 100;
    let weapon_id = weapon_id - level;
    if let Some(weapon) = WEAPON_MAP.get(&weapon_id) {
      return Self {
        weapon_id: weapon_id,
        level: level.try_into().unwrap(),
        name: weapon.name.clone(),
        icon_id: weapon.icon_id,
        wep_type: weapon.wep_type,
      };
    } else {
      eprintln!("unknown weaponid {weapon_id}");
      return Self {
        weapon_id: weapon_id,
        ..Default::default()
      };
    }
  }
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct WeaponInfos {
  pub lefthand: Vec<WeaponInfo>,
  pub righthand: Vec<WeaponInfo>,
}

impl From<&EquippedArmamentsAndItems> for WeaponInfos {
  fn from(equipped: &EquippedArmamentsAndItems) -> Self {
    let mut lefthand = Vec::new();
    let mut righthand = Vec::new();
    lefthand.push(WeaponInfo::new(&equipped.left_hand_armament1));
    lefthand.push(WeaponInfo::new(&equipped.left_hand_armament2));
    lefthand.push(WeaponInfo::new(&equipped.left_hand_armament3));
    righthand.push(WeaponInfo::new(&equipped.right_hand_armament1));
    righthand.push(WeaponInfo::new(&equipped.right_hand_armament2));
    righthand.push(WeaponInfo::new(&equipped.right_hand_armament3));
    Self {
      lefthand: lefthand,
      righthand: righthand,
    }
  }
}

impl MyState {
  pub fn get_equipped_weapon_info(&self, selected: usize) -> Result<WeaponInfos> {
    let save = self.save.lock().unwrap();
    let Some(save) = Option::as_ref(&save) else {
      anyhow::bail!("no save loaded");
    };
    let equipped = &save.user_data_x[selected].equipped_armaments_and_items;
    let weapon_infos = WeaponInfos::from(equipped);
    Ok(weapon_infos)
  }
}

#[cfg(test)]
mod test {

  #[test]
  fn test_load_save() {
    let path = "C:/Users/breezing/AppData/Roaming/EldenRing/76561198070426256/ER0000.sl2";
    // let path = "C:/Users/breezing/AppData/Roaming/EldenRing/76561198070426256 - 烧树前/ER0000.sl2";
    let save = er_save_lib::Save::from_path(path).unwrap();
    let equipped = &save.user_data_x[1].equipped_armaments_and_items;
    let weapon_info = crate::weapon::WeaponInfos::from(equipped);
    println!("weapon_info : {weapon_info:?}");
    let version = save.user_data_11.version;
    let size = save.user_data_11.size;
    println!("version : {version} \n size : {size}")
  }
}
