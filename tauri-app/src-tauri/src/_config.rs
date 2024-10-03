
#[derive(Debug, Clone, serde::Deserialize)]
struct ProjectConfig {
  helper: Config,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct Config {
  file: String,
}

#[allow(unused_imports)]
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

fn setup() -> Config {
  init_tracing();
  enter_project_root();
  tracing::info!("cwd: {}", std::env::current_dir().unwrap().display());
  let config: ProjectConfig = toml::from_str(&std::fs::read_to_string("config.toml").unwrap()).unwrap();
  config.helper
}
