pub mod equips;
pub mod meta_info;
pub mod events;

pub use equips::EquippedInfos;
pub use meta_info::MetaInfo;
pub use events::EventInfos;

use crate::{sync::MyState, Result};

impl MyState {
  pub fn decode_meta_info(&self) -> Result<MetaInfo> {
    self.decode_from_save_with_cache::<MetaInfo>()
  }
}
