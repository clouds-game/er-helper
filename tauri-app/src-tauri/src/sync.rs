use std::{path::PathBuf, sync::{atomic::{AtomicU64, AtomicUsize, Ordering}, Mutex}};

use crate::{cache::Cache, Result};


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
  pub _selected: AtomicUsize,
  pub save: Mutex<Option<er_save_lib::Save>>,
  pub loaded_time: AtomicU64,
  pub cache: Cache<u64>,
  pub selected_cache: Cache<(u64, usize)>,
}

impl MyState {
  pub fn new(path: PathBuf) -> Self {
    Self {
      save_path: path,
      _selected: AtomicUsize::new(usize::MAX),
      ..Default::default()
    }
  }

  pub fn selected(&self) -> usize {
    self._selected.load(Ordering::SeqCst)
  }
  pub fn set_selected(&self, value: usize) {
    let version = self.loaded_version();
    self.selected_cache.set_key((version, value));
    self._selected.store(value, Ordering::SeqCst)
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
    self.cache.set_key(meta.last_modified);
    self.loaded_time.store(meta.last_modified, Ordering::SeqCst);
    Ok(())
  }

  pub fn is_loaded_latest(&self) -> bool {
    let Ok(meta) = self.sync_metadata() else { return false };
    self.loaded_time.load(Ordering::SeqCst) > meta.last_modified
  }

  pub fn get_metadata(&self) -> Metadata {
    self.metadata.lock().unwrap().clone()
  }

  pub fn loaded_version(&self) -> u64 {
    self.loaded_time.load(Ordering::SeqCst)
  }

  pub fn get_from_cache<T: 'static + Clone + Send>(&self) -> Option<T> {
    let current_version = self.loaded_version();
    let (ref_, _) = self.cache.get::<T>(current_version);
    ref_.map(|i| i.clone())
  }

  pub fn get_from_cache_or_save<T: 'static + Clone + Send + Sync>(&self) -> Result<T>
  where
    T: for<'a> TryFrom<&'a er_save_lib::Save>,
    for<'a> <T as TryFrom<&'a er_save_lib::Save>>::Error: std::fmt::Display,
  {
    if let Some(value) = self.get_from_cache::<T>() {
      return Ok(value);
    }
    let current_version = self.loaded_version();
    let save = self.save.lock().unwrap();
    let Some(save) = save.as_ref() else {
      anyhow::bail!("no save loaded");
    };
    info!("convert from save and save cache: {} (version: {})", std::any::type_name::<T>(), current_version);
    let value = match T::try_from(save) {
      Ok(value) => value,
      Err(e) => anyhow::bail!("failed to convert save to {}: {}", std::any::type_name::<T>(), e),
    };
    self.cache.insert(current_version, value.clone());
    Ok(value)
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
