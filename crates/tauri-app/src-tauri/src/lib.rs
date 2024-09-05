use std::{path::Path, sync::Mutex};

#[derive(Default)]
struct MyState {
  selected: Mutex<String>,
}
impl MyState {
  pub fn new() -> Self {
    Self {
      selected: Mutex::new("miao".to_string())
    }
  }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicInfo {
  pub nickname: String,
  pub game_name: String,
  pub duration: u64,
  pub steam_id: String,
}

#[tauri::command]
async fn get_basic_info(state: tauri::State<'_, MyState>) -> Result<BasicInfo, String> {
  let selected_name = state.selected.lock().unwrap().clone();
  Ok(BasicInfo {
    nickname: "hello".to_string(),
    game_name: selected_name,
    duration: 100_000,
    steam_id: "AABBCDDD".to_string(),
  })
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicPlayerInfo {
  pub level: u64,
  pub rune: u64,
  pub boss: u64,
  pub place: u64,
  pub death: u64,
}

#[tauri::command]
async fn get_player_info(state: tauri::State<'_, MyState>, selected: Option<String>) -> Result<BasicPlayerInfo, String> {
  let current = if let Some(selected) = selected {
    *state.selected.lock().unwrap() = selected.clone();
    selected
  } else {
    state.selected.lock().unwrap().clone()
  };
  Ok(BasicPlayerInfo {
    level: 900,
    rune: 300_000,
    boss: 99,
    place: 250,
    death: 1500,
  })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run<P: AsRef<Path>>(path: P) {
  println!("running on file: {}", path.as_ref().display());
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .manage(MyState::new())
    .invoke_handler(tauri::generate_handler![
      get_basic_info,
      get_player_info,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
