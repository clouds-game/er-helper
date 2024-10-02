use crate::{sync::MyState, Result};
use er_save_lib::save::user_data_x::EquippedArmamentsAndItems;

#[derive(Default, Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct WeaponInfo {
  pub id: u32,
  pub level: u8,
}

impl WeaponInfo {
  pub fn new(id: &u32) -> Self {
    let level = id % 100;
    let id = id - level;
    Self {
      id,
      level: level as _,
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
      lefthand, righthand,
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
  include!("_config.rs");

  #[test]
  fn test_load_save() {
    let config = setup();
    let save = er_save_lib::Save::from_path(config.file).unwrap();
    let equipped = &save.user_data_x[0].equipped_armaments_and_items;
    let weapon_info = crate::weapon::WeaponInfos::from(equipped);
    println!("weapon_info: {:?}", weapon_info);
  }
}
