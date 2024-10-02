use std::collections::HashMap;

use lazy_static::lazy_static;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Database<D, T> {
  pub count: usize,
  pub data: Vec<D>,
  pub text: HashMap<String, Option<T>>,
}

pub type GraceDb = Database<Grace, Text>;
pub type BossDb = Database<Boss, Text>;
pub type WeaponDb = Database<Weapon, Text>;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Text {
  pub name: HashMap<u32, Option<String>>,
  #[serde(skip_serializing_if="HashMap::is_empty", default)]
  pub map_name: HashMap<u32, Option<String>>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Grace {
  pub id: u32,
  pub map_id: u32,
  pub block: u32,
  pub offset: u32,
  pub bit_mask: u8,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Boss {
  pub id: u32,
  pub map_text_id: u32,
  pub block: u32,
  pub offset: u32,
  pub bit_mask: u8,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Weapon {
  pub id: u32,
  #[serde(alias = "type")]
  pub wep_type: u16,
  pub icon_id: u16,
  #[serde(alias = "path")]
  pub icon_path: String,
}

lazy_static!{
  pub static ref GRACES: GraceDb = serde_json::from_str(include_str!("../../assets/grace.out.json")).unwrap();
  pub static ref BOSS: BossDb = serde_json::from_str(include_str!("../../assets/boss.out.json")).unwrap();
  pub static ref WEAPON: WeaponDb = serde_json::from_str(include_str!("../../assets/weapon.out.json")).unwrap();
}

#[test]
fn test_load_db() {
  println!("graces: {:?}", GRACES.count);
  println!("boss: {:?}", BOSS.count);
  println!("weapon: {:?}", WEAPON.count);
}
