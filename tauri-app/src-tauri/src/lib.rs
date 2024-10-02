#[macro_use] extern crate tracing;

pub mod db;
pub mod sync;
pub mod save;
pub mod weapon;
pub mod downloader;
pub mod cache;

use std::{path::Path, sync::{mpsc, Arc}};

use downloader::Downloader;
use sync::{Metadata, MyState};

use anyhow::Result;

#[tauri::command]
async fn get_metadata(state: tauri::State<'_, Arc<MyState>>) -> Result<Metadata, String> {
  Ok(state.get_metadata())
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicInfo {
  pub steam_id: String,
  pub role_name: String,
  pub duration: u64,
  pub level: u64,
  pub rune: u64,
  pub boss: u64,
  pub grace: u64,
  pub death: u64,
  pub attrs: [u32; 8],
  pub hp: [u32; 3],
  pub fp: [u32; 3],
  pub sp: [u32; 3],
}

#[tauri::command]
async fn get_basic_info(state: tauri::State<'_, Arc<MyState>>, selected: Option<usize>) -> Result<BasicInfo, String> {
  if let Some(selected) = selected {
    state.selected.store(selected, std::sync::atomic::Ordering::SeqCst);
  };
  let selected = state.get_selected();
  state.get_basic_info(selected).map_err(|e| format!("state.get_basic_info: {}", e))
}

#[tauri::command(rename_all = "snake_case")]
async fn get_equipped_weapon_info(state: tauri::State<'_, Arc<MyState>>) -> Result<crate::weapon::WeaponInfos, String> {
  let selected = state.get_selected();
  state.get_equipped_weapon_info(selected).map_err(|e| format!("state.get_equipped_weapon_info: {}", e))
}

#[tauri::command(rename_all = "snake_case")]
async fn get_icons(sender: tauri::State<'_, mpsc::Sender<downloader::Task>>, icon_ids: Vec<u32>) -> Result<Vec<String>, String> {
  use base64::Engine as _;
  let mut icons = Vec::new();
  for icon_id in icon_ids {
    let icon_path = format!("tauri-app/assets/icons/icon_{:05}.png", icon_id);
    if !Path::new(&icon_path).exists() {
      sender.send(downloader::Task {
        path: icon_path.clone(),
        url: format!("https://assets.erdb.workers.dev/icons/armaments/{:05}/menu", icon_id)
      }).ok();
    }
    let data = std::fs::read(icon_path).unwrap_or_default();
    let icon = base64::engine::general_purpose::STANDARD.encode(data);
    icons.push(format!("data:image/png;base64,{}", icon));
  }
  Ok(icons)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run<P: AsRef<Path>>(path: P) {
  info!("running on file: {}", path.as_ref().display());
  let my_state = Arc::new(MyState::new(path.as_ref().to_path_buf()));
  let downloader = Downloader::new();
  let downloader_tx = downloader.tx.clone();
  std::thread::spawn(move || downloader.run());
  std::thread::spawn({
    let state = my_state.clone();
    move || sync::background(state)
  });
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .manage(my_state)
    .manage(downloader_tx)
    .invoke_handler(tauri::generate_handler![
      get_metadata,
      get_basic_info,
      get_equipped_weapon_info,
      get_icons,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
