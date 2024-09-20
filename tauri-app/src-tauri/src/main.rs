// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[derive(Debug, Clone, serde::Deserialize)]
struct ProjectConfig {
  helper: Config,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct Config {
  file: String,
}
fn init_tracing() {
  use tracing_subscriber::{EnvFilter, fmt::format::FmtSpan};
  tracing_subscriber::fmt()
    // .with_env_filter(EnvFilter::from_env("info"))
    .with_span_events(FmtSpan::CLOSE)
    .init();
}

fn enter_project_root() {
  let mut path = std::env::current_exe().unwrap();
  while !path.join("pixi.toml").exists() {
    path = path.parent().unwrap().to_path_buf();
  }
  std::env::set_current_dir(path).unwrap();
}

fn main() {
  init_tracing();
  enter_project_root();
  tracing::info!("cwd: {}", std::env::current_dir().unwrap().display());
  let s = std::fs::read_to_string("config.toml").unwrap();
  let config: ProjectConfig = toml::from_str(&s).unwrap();
  tauri_app_lib::run(config.helper.file)
}
