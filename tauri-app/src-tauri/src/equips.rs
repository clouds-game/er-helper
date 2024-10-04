use er_save_lib::save::user_data_x::UserDataX;

#[derive(Default, Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct WeaponInfo {
  pub id: u32,
  pub level: u8,
}

#[derive(Default, Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SpellInfo {
  pub id: u32,
}

impl WeaponInfo {
  pub fn new(id: u32) -> Self {
    let level = id % 100;
    let id = id - level;
    Self {
      id,
      level: level as _,
    }
  }
}

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct EquippedInfos {
  pub lefthand: Vec<WeaponInfo>,
  pub righthand: Vec<WeaponInfo>,
  pub arrows: Vec<WeaponInfo>,
  pub bolts: Vec<WeaponInfo>,
  pub magics: Vec<SpellInfo>,
}

impl From<&UserDataX> for EquippedInfos {
  fn from(userdata_x: &UserDataX) -> Self {
    let equipped = &userdata_x.equipped_armaments_and_items;
    let lefthand = [equipped.left_hand_armament1, equipped.left_hand_armament2, equipped.left_hand_armament3];
    let righthand = [equipped.right_hand_armament1, equipped.right_hand_armament2, equipped.right_hand_armament3];
    let arrows = [equipped.arrows1, equipped.arrows2];
    let bolts = [equipped.bolts1, equipped.bolts2];
    Self {
      lefthand: lefthand.into_iter().map(WeaponInfo::new).collect(),
      righthand: righthand.into_iter().map(WeaponInfo::new).collect(),
      arrows: arrows.into_iter().map(WeaponInfo::new).collect(),
      bolts: bolts.into_iter().map(WeaponInfo::new).collect(),
      magics: userdata_x.equipped_spells.spellslot.iter().map(|spell| SpellInfo { id: spell.spell_id }).collect(),
    }
  }
}

#[cfg(test)]
mod test {
  include!("_config.rs");

  #[test]
  fn test_load_save() {
    let config = setup();
    let save = er_save_lib::Save::from_path(config.file).unwrap();
    let equipped_info = crate::equips::EquippedInfos::from(&save.user_data_x[0]);
    println!("weapon_info: {:?}", equipped_info);
  }
}
