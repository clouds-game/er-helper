use std::{collections::HashSet, io::Write, path::Path, sync::{mpsc, Arc, Mutex}};
use std::fs::File;

pub struct Downloader {
  pub tx: mpsc::Sender<Task>,
  rx: mpsc::Receiver<Task>,
  pub state: Arc<Mutex<DownloadState>>,
}

#[derive(Default)]
pub struct DownloadState {
  pub queue: Vec<Task>,
  pub set: HashSet<String>,
}

pub struct Task {
  pub path: String,
  pub url: String,
}

impl Downloader {
  pub fn new() -> Self {
    let (tx, rx) = mpsc::channel();
    Self { tx, rx, state: Default::default() }
  }

  pub fn run(&self) {
    let state= self.state.clone();
    std::thread::spawn(move || {
      loop {
        let task = {
          state.lock().unwrap().queue.pop()
        };

        if let Some(task) = task {
          // download task
          if let Err(e) = download_file(&task.url, &task.path) {
            eprintln!("Failed to download {}: {}", task.url, e);
          }

          state.lock().unwrap().set.remove(&task.url);
        }
      }
    });

    for task in self.rx.iter() {
      let mut state = self.state.lock().unwrap();
      if state.set.contains(&task.url) {
        continue;
      }
      state.set.insert(task.url.clone());
      state.queue.push(task);
    }
  }
}

fn download_file(url: &str, path: &str) -> Result<(), Box<dyn std::error::Error>> {
  println!("Downloading from {} to {}", url, path);
  let buffer = reqwest::blocking::get(url)?.bytes()?;
  if let Some(parent) = Path::new(path).parent() {
    std::fs::create_dir_all(parent)?;
  }
  let mut out = File::create(path)?;
  out.write(buffer.as_ref())?;
  Ok(())
}
