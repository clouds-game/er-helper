#[macro_use] extern crate tracing;

pub mod db;
pub mod sync;
pub mod save;

use std::{path::Path, sync::Arc};

use sync::{Metadata, MyState};

use anyhow::Result;

#[tauri::command]
async fn get_metadata(state: tauri::State<'_, Arc<MyState>>) -> Result<Metadata, String> {
  Ok(state.get_metadata())
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicInfo {
  pub nickname: String,
  pub role_name: String,
  pub duration: u64,
  pub steam_id: String,
}

#[tauri::command]
async fn get_basic_info(state: tauri::State<'_, Arc<MyState>>) -> Result<BasicInfo, String> {
  let selected = state.get_selected();
  state.get_basic_info(selected).map_err(|e| format!("state.get_basic_info: {}", e))
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicPlayerInfo {
  pub level: u64,
  pub rune: u64,
  pub boss: u64,
  pub grace: u64,
  pub death: u64,
}

#[tauri::command]
async fn get_player_info(state: tauri::State<'_, Arc<MyState>>, selected: Option<usize>) -> Result<BasicPlayerInfo, String> {
  if let Some(selected) = selected {
    state.selected.store(selected, std::sync::atomic::Ordering::SeqCst);
  };
  let selected = state.get_selected();
  state.get_player_info(selected).map_err(|e| format!("state.get_player_info: {}", e))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run<P: AsRef<Path>>(path: P) {
  info!("running on file: {}", path.as_ref().display());
  let my_state = Arc::new(MyState::new(path.as_ref().to_path_buf()));
  std::thread::spawn({
    let state = my_state.clone();
    move || sync::background(state)
  });
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .manage(my_state)
    .invoke_handler(tauri::generate_handler![
      get_metadata,
      get_basic_info,
      get_player_info,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}