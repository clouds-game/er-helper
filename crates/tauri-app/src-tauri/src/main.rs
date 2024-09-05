// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct Config {
  file: String,
}

fn main() {
  println!("cwd: {}", std::env::current_dir().unwrap().display());
  let s = std::fs::read_to_string("er.toml").unwrap();
  let config: Config = toml::from_str(&s).unwrap();
  tauri_app_lib::run(config.file)
}
