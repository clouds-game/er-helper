use std::collections::HashMap;

use er_save_lib::save::user_data_x::UserDataX;

use crate::{db::{BOSS, GRACES}, Result};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BossInfo {
  pub id: u32,
  pub flag_id: u32,
  pub defeated: bool,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct GraceInfo {
  pub id: u32,
  pub flag_id: u32,
  pub activated: bool,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct EventInfos {
  boss: Vec<BossInfo>,
  grace: Vec<GraceInfo>,
}

impl TryFrom<&UserDataX> for EventInfos {
  type Error = anyhow::Error;

  fn try_from(value: &UserDataX) -> Result<Self, Self::Error> {
    let events = &value.event_flags;
    let boss = BOSS.data.iter()
      .filter(|i| events[i.offset as usize] & i.bit_mask != 0)
      .map(|i| BossInfo {
        id: i.id,
        flag_id: i.eventflag_id,
        defeated: true,
      })
      .collect::<Vec<_>>();
    let grace = GRACES.data.iter()
      .filter(|i| events[i.offset as usize] & i.bit_mask != 0)
      .map(|i| GraceInfo {
        id: i.id,
        flag_id: i.eventflag_id,
        activated: true,
      })
      .collect::<Vec<_>>();
    Ok(Self {
      boss, grace,
    })
  }
}

pub struct Events {
  pub events: Vec<u8>,
  pub graces: HashMap<u32, bool>,
  pub bosses: HashMap<u32, bool>,
}

impl std::fmt::Debug for Events {
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
    f.debug_struct("Events").field("events", &self.events.len()).field("graces", &self.graces.len()).field("bosses", &self.bosses.len()).finish()
  }
}

impl TryFrom<&UserDataX> for Events {
  type Error = anyhow::Error;

  // #[instrument(skip(userdata))]
  fn try_from(userdata: &UserDataX) -> Result<Self> {
    let events = userdata.event_flags.clone();
    let mut graces = HashMap::new();
    for i in GRACES.data.iter() {
      let flag = events[i.offset as usize] & i.bit_mask != 0;
      graces.insert(i.id, flag);
    }
    let mut bosses = HashMap::new();
    for i in BOSS.data.iter() {
      let flag = events[i.offset as usize] & i.bit_mask != 0;
      bosses.insert(i.id, flag);
    }
    Ok(Self {
      events, graces, bosses,
    })
  }
}
