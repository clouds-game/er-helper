// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

include!("_config.rs");

fn main() {
  let config = setup();
  tauri_app_lib::run(config.file)
}
