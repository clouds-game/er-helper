
// https://github.com/CyberGiant7/Elden-Ring-Automatic-Checklist/blob/main/assets/js/script.js

use std::io::Read;

use anyhow::Result;

fn main() -> Result<()> {
  let mut file = std::fs::File::open("/tmp/ER0000.sl2")?;
  let mut data = Vec::new();
  file.read_to_end(&mut data)?;
  let save = er_save_lib::Save::from_slice(&data)?;
  println!("header: {:?}", save.user_data_10.profile_summary.profiles[0]);
  println!("steam_id: {}", save.user_data_10.steam_id);
  println!("names: {:?}", save.user_data_10.profile_summary.profiles[0].character_name);
  Ok(())
}
