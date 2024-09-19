use lazy_static::lazy_static;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Grace {
  pub id: u32,
  pub map: String,
  pub text: String,
  pub block: u32,
  pub block_idx: u32,
  pub offset: u32,
  pub bit_mask: u8,
}

lazy_static!{
  pub static ref GRACES: Vec<Grace> = serde_json::from_str(include_str!("../assets/graces.out.json")).unwrap();
}

#[test]
fn test_load_csv() {
  println!("graces: {:?}", GRACES.len());
}
