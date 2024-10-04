use std::{any::TypeId, ops::Deref, sync::Mutex};

use dashmap::DashMap as HashMap;

pub type BoxAny = Box<dyn std::any::Any + Send + Sync>;

pub struct CacheItem<K> {
  pub data: BoxAny,
  pub version: K,
}

#[derive(Default)]
pub struct Cache<K> {
  key: Mutex<K>,
  inner: HashMap<std::any::TypeId, CacheItem<K>>,
}

pub struct Ref<'a, K, T> {
  inner: dashmap::mapref::one::Ref<'a, std::any::TypeId, CacheItem<K>>,
  _phantom: std::marker::PhantomData<T>,
}

impl<'a, K, T: 'static> Ref<'a, K, T> {
  pub fn new(inner: dashmap::mapref::one::Ref<'a, std::any::TypeId, CacheItem<K>>) -> Option<Self> {
    if inner.value().data.type_id() == std::any::TypeId::of::<T>() {
      Some(Self {
        inner,
        _phantom: std::marker::PhantomData,
      })
    } else {
      None
    }
  }
}

impl<'a, K, T: 'static> Deref for Ref<'a, K, T> {
  type Target = T;

  fn deref(&self) -> &Self::Target {
    self.inner.data.downcast_ref::<T>().unwrap()
  }
}

impl<K: PartialEq + Copy> Cache<K> {
  pub fn new(key: K) -> Self {
    Self {
      key: Mutex::new(key),
      inner: HashMap::new(),
    }
  }

  fn check_version(&self, key: K) -> bool {
    *self.key.lock().unwrap() == key
  }

  pub fn set_key(&self, new_key: K) {
    let mut key = self.key.lock().unwrap();
    if *key != new_key {
      self.inner.clear();
      *key = new_key;
    }
  }

  pub fn clear(&self, key: K) {
    if self.check_version(key) {
      self.inner.clear();
    }
  }

  pub fn insert<T: Send + Sync + 'static>(&self, version: K, value: T) {
    if !self.check_version(version) { return }
    let type_id = std::any::TypeId::of::<T>();
    if self.get_version(type_id) == Some(version) {
      return
    }
    self.inner.insert(type_id, CacheItem {
      data: Box::new(value),
      version
    });
  }

  pub fn get_version(&self, type_id: TypeId) -> Option<K> {
    self.inner.get(&type_id).map(|i| i.version)
  }

  pub fn get<'a, T: Send + 'static>(&'a self, version: K) -> (Option<Ref<'a, K, T>>, Option<K>) {
    let type_id = std::any::TypeId::of::<T>();
    let item = self.inner.get(&type_id);
    let old_version = item.as_ref().map(|i| i.version);
    if old_version == Some(version) {
      (item.and_then(Ref::new), old_version)
    } else {
      (None, old_version)
    }
  }
}
