use std::{path::PathBuf, sync::{atomic::{AtomicU64, AtomicUsize, Ordering}, Mutex}};

use crate::Result;


#[derive(Debug, Default, Clone, serde::Serialize, serde::Deserialize)]
pub struct Metadata {
  pub exists: bool,
  pub last_modified: u64,
  pub size: u64,
}

#[derive(Default)]
pub struct MyState {
  pub save_path: PathBuf,
  pub metadata: Mutex<Metadata>,
  pub selected: AtomicUsize,
  pub save: Mutex<Option<er_save_lib::Save>>,
  pub loaded_time: AtomicU64,
}

impl MyState {
  pub fn new(path: PathBuf) -> Self {
    Self {
      save_path: path,
      selected: AtomicUsize::new(usize::MAX),
      ..Default::default()
    }
  }

  pub fn sync_metadata(&self) -> Result<Metadata> {
    let mut metadata = Metadata::default();
    if let Ok(meta) = std::fs::metadata(&self.save_path) {
      metadata.exists = true;
      metadata.last_modified = meta.modified()?.duration_since(std::time::SystemTime::UNIX_EPOCH)?.as_secs();
      metadata.size = meta.len();
    } else {
      metadata.exists = false;
    }
    *self.metadata.lock().unwrap() = metadata.clone();
    Ok(metadata)
  }

  pub fn load_save(&self) -> Result<()> {
    let meta = self.sync_metadata()?;
    let save = er_save_lib::Save::from_path(&self.save_path)?;
    *self.save.lock().unwrap() = Some(save);
    self.loaded_time.store(meta.last_modified, Ordering::Relaxed);
    Ok(())
  }

  pub fn is_loaded_latest(&self) -> bool {
    let Ok(meta) = self.sync_metadata() else { return false };
    self.loaded_time.load(Ordering::Relaxed) > meta.last_modified
  }

  pub fn get_metadata(&self) -> Metadata {
    self.metadata.lock().unwrap().clone()
  }
}

pub fn background(state: std::sync::Arc<MyState>) {
  loop {
    if state.is_loaded_latest() {
      std::thread::sleep(std::time::Duration::from_millis(500));
      continue;
    }
    if let Err(e) = state.load_save() {
      eprintln!("Error loading save: {}", e);
    }
    std::thread::sleep(std::time::Duration::from_millis(3000));
  }
}
