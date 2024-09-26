use std::collections::HashMap;

use lazy_static::lazy_static;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Grace {
  pub id: u32,
  pub map: String,
  pub name: String,
  pub block: u32,
  pub block_idx: u32,
  pub offset: u32,
  pub bit_mask: u8,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Boss {
  pub id: u32,
  pub map: String,
  pub name: String,
  pub block: u32,
  pub block_idx: u32,
  pub offset: u32,
  pub bit_mask: u8,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Weapon {
  pub id: u32,
  pub name: String,
  pub icon_id: u16,
  pub wep_type: u16,
}

lazy_static!{
  pub static ref GRACES: Vec<Grace> = serde_json::from_str(include_str!("../assets/graces.out.json")).unwrap();
  pub static ref BOSS: Vec<Boss> = serde_json::from_str(include_str!("../assets/boss.out.json")).unwrap();
  pub static ref WEAPON: Vec<Weapon> = serde_json::from_str(include_str!("../assets/weapon.out.json")).unwrap();
  pub static ref WEAPON_MAP: HashMap<u32, Weapon> = {
    let mut map = HashMap::new();
    for weapon in WEAPON.iter() {
      map.insert(weapon.id, weapon.clone());
    }
    map
  };
}

#[test]
fn test_load_db() {
  println!("graces: {:?}", GRACES.len());
  println!("boss: {:?}", BOSS.len());
}
