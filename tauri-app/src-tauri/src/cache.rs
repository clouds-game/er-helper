use std::ops::Deref;

use dashmap::DashMap as HashMap;

pub type BoxAny = Box<dyn std::any::Any + Send + Sync>;

#[derive(Default)]
pub struct Cache {
  inner: HashMap<std::any::TypeId, BoxAny>,
  version: HashMap<std::any::TypeId, u64>,
}

pub struct Ref<'a, T> {
  inner: dashmap::mapref::one::Ref<'a, std::any::TypeId, BoxAny>,
  _phantom: std::marker::PhantomData<T>,
}

impl<'a, T: 'static> Ref<'a, T> {
  pub fn new(inner: dashmap::mapref::one::Ref<'a, std::any::TypeId, BoxAny>) -> Option<Self> {
    if inner.value().type_id() == std::any::TypeId::of::<T>() {
      Some(Self {
        inner,
        _phantom: std::marker::PhantomData,
      })
    } else {
      None
    }
  }
}

impl<'a, T: 'static> Deref for Ref<'a, T> {
  type Target = T;

  fn deref(&self) -> &Self::Target {
    self.inner.downcast_ref::<T>().unwrap()
  }
}

impl Cache {
  pub fn new() -> Self {
    Self {
      inner: HashMap::new(),
      version: HashMap::new(),
    }
  }

  pub fn insert<T: Send + Sync + 'static>(&self, value: T, version: u64) {
    let type_id = std::any::TypeId::of::<T>();
    if self.get_version(type_id) > version {
      return;
    }
    self.inner.insert(type_id, Box::new(value));
    self.version.insert(type_id, version);
  }

  pub fn get<'a, T: Send + 'static>(&'a self, version: Option<u64>) -> (Option<Ref<'a, T>>, u64) {
    let type_id = std::any::TypeId::of::<T>();
    let old_version = self.get_version(type_id);
    if let Some(version) = version {
      if old_version > version {
        return (None, old_version);
      }
    }
    (self.inner.get(&type_id).and_then(Ref::new), old_version)
  }

  fn get_version(&self, type_id: std::any::TypeId) -> u64 {
    self.version.get(&type_id).map(|i| *i).unwrap_or_default()
  }
}
